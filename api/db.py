"""Peewee/SQLite persistence layer for the ecommerce data model.

Replaces the previous in-memory dict database. Exposes ``ECOMMERCE_DB``, a
dict-like facade over the peewee models so existing call sites (including
agent-authored report tools that do ``ECOMMERCE_DB["orders"].values()``)
keep working unchanged.
"""

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from uuid import uuid4

from peewee import (
    CharField,
    CompositeKey,
    FloatField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)
from playhouse.pydantic_utils import to_pydantic

DB_PATH = os.getenv(
    "DB_PATH", os.path.join(os.path.dirname(__file__), "ecommerce.db")
)

database = SqliteDatabase(
    DB_PATH,
    pragmas={"journal_mode": "wal", "foreign_keys": 1},
)


class BaseModel(Model):
    class Meta:
        database = database


class Product(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()
    price = FloatField()
    stock = IntegerField(default=0)
    sku = CharField(null=True)
    seller_id = CharField(null=True)
    created_at = CharField()
    updated_at = CharField()


class Customer(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()
    email = CharField(unique=True)
    created_at = CharField()
    updated_at = CharField()


class Order(BaseModel):
    id = CharField(primary_key=True)
    customer_id = CharField()
    items = TextField()  # JSON-encoded list[dict]
    total = FloatField()
    status = CharField()
    invoice_id = CharField(null=True)
    seller_id = CharField(null=True)
    created_at = CharField()
    updated_at = CharField()


class ApiCredential(BaseModel):
    """HTTP Basic Auth credentials for accessing the API.

    ``username`` is the customer's email for customer-owned credentials.
    ``customer`` is null for non-customer (e.g. admin) credentials.
    """

    username = CharField(primary_key=True)
    password_hash = CharField()
    salt = CharField()
    customer = ForeignKeyField(
        Customer, backref="api_credentials", null=True, unique=True
    )
    created_at = CharField()
    updated_at = CharField()


class ChatHistory(BaseModel):
    """Represents a user chat session. User's can have one or more chat session"""

    session_id = CharField()
    agent_id = CharField()
    user = ForeignKeyField(Customer, backref="chat_history")
    label = CharField()

    class Meta:
        primary_key = CompositeKey("session_id", "user")


def _chat_history_to_dict(row: ChatHistory) -> dict:
    return {
        "session_id": row.session_id,
        "agent_id": row.agent_id,
        "user_id": row.user.id,
        "label": row.label,
    }


def _product_to_dict(row: Product) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "price": row.price,
        "stock": row.stock,
        "sku": row.sku,
        "seller_id": row.seller_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _customer_to_dict(row: Customer) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "email": row.email,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _order_to_dict(row: Order) -> dict:
    return {
        "id": row.id,
        "customer_id": row.customer_id,
        "items": json.loads(row.items),
        "total": row.total,
        "status": row.status,
        "invoice_id": row.invoice_id,
        "seller_id": row.seller_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _order_from_dict(data: dict) -> dict:
    return {**data, "items": json.dumps(data["items"])}


class _TableView:
    """dict-like view over a peewee model, keyed by ``id``."""

    def __init__(self, model, to_dict, from_dict=lambda d: d):
        self._model = model
        self._to_dict = to_dict
        self._from_dict = from_dict

    def __getitem__(self, key):
        row = self._model.get_or_none(self._model.id == key)
        if row is None:
            raise KeyError(key)
        return self._to_dict(row)

    def __setitem__(self, key, value):
        data = self._from_dict(dict(value))
        data["id"] = key
        self._model.insert(**data).on_conflict_replace().execute()

    def __delitem__(self, key):
        self._model.delete().where(self._model.id == key).execute()

    def __contains__(self, key):
        return self._model.get_or_none(self._model.id == key) is not None

    def __len__(self):
        return self._model.select().count()

    def values(self):
        return [self._to_dict(row) for row in self._model.select()]

    def keys(self):
        return [row.id for row in self._model.select()]

    def items(self):
        return [(row.id, self._to_dict(row)) for row in self._model.select()]

    def get(self, key, default=None):
        row = self._model.get_or_none(self._model.id == key)
        return self._to_dict(row) if row is not None else default


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Return ``(password_hash, salt)`` using PBKDF2-HMAC-SHA256."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000
    )
    return digest.hex(), salt


def set_api_credential(username: str, password: str) -> None:
    """Create or update the password for an API user."""
    now = datetime.now(timezone.utc).isoformat()
    password_hash, salt = _hash_password(password)
    ApiCredential.insert(
        username=username,
        password_hash=password_hash,
        salt=salt,
        created_at=now,
        updated_at=now,
    ).on_conflict(
        conflict_target=[ApiCredential.username],
        update={
            ApiCredential.password_hash: password_hash,
            ApiCredential.salt: salt,
            ApiCredential.updated_at: now,
        },
    ).execute()


def create_customer_account(name: str, email: str, password: str) -> dict:
    """Create a Customer and its linked ApiCredential (username = email).

    Raises ValueError if the email is already registered.
    """
    normalized_email = email.strip().lower()
    if Customer.get_or_none(Customer.email == normalized_email) is not None:
        raise ValueError("A customer with this email already exists.")
    if api_credential_exists(normalized_email):
        raise ValueError("A customer with this email already exists.")

    now = datetime.now(timezone.utc).isoformat()
    password_hash, salt = _hash_password(password)

    with database.atomic():
        customer = Customer.create(
            id=f"cust_{uuid4().hex[:8]}",
            name=name.strip(),
            email=normalized_email,
            created_at=now,
            updated_at=now,
        )
        ApiCredential.create(
            username=normalized_email,
            password_hash=password_hash,
            salt=salt,
            customer=customer,
            created_at=now,
            updated_at=now,
        )

    return _customer_to_dict(customer)


def list_customers() -> list[dict]:
    """Return all customers, newest first."""
    rows = Customer.select().order_by(Customer.created_at.desc())
    return [_customer_to_dict(row) for row in rows]


def delete_customer_account(customer_id: str) -> bool:
    """Delete a Customer along with its ApiCredential and chat sessions.

    Returns False if no customer with this id exists.
    """
    customer = Customer.get_or_none(Customer.id == customer_id)
    if customer is None:
        return False

    with database.atomic():
        ApiCredential.delete().where(ApiCredential.customer == customer).execute()
        ChatHistory.delete().where(ChatHistory.user == customer).execute()
        customer.delete_instance()

    return True


def api_credential_exists(username: str) -> bool:
    """Return True if an API user with this username already exists."""
    return ApiCredential.get_or_none(ApiCredential.username == username) is not None


def verify_api_credential(username: str, password: str) -> bool:
    """Check a username/password pair against the stored, hashed credential."""
    credential = ApiCredential.get_or_none(ApiCredential.username == username)
    if credential is None:
        return False
    computed_hash, _ = _hash_password(password, credential.salt)
    return hmac.compare_digest(computed_hash, credential.password_hash)


def _seed_default_api_credential() -> None:
    """Seed a default API user from env vars on first run, if none exist."""
    if ApiCredential.select().count() > 0:
        return
    default_username = os.getenv("API_USERNAME", "admin")
    default_password = os.getenv("API_PASSWORD", "admin123")
    set_api_credential(default_username, default_password)


def _migrate_api_credential_customer_column() -> None:
    """Add the ``customer_id`` column to a pre-existing apicredential table."""
    if "apicredential" not in database.get_tables():
        return
    columns = {col.name for col in database.get_columns("apicredential")}
    if "customer_id" not in columns:
        database.execute_sql(
            "ALTER TABLE apicredential ADD COLUMN customer_id VARCHAR(255) "
            "REFERENCES customer (id)"
        )


def create_chat_session(
    session_id: str, agent_id: str, user: Customer, chat_label: str
) -> ChatHistory:
    return (
        ChatHistory.insert(
            session_id=session_id, agent_id=agent_id, user=user, label=chat_label
        )
        .returning(ChatHistory)
        .on_conflict_ignore()
        .execute()
    )


def list_chat_sessions(user: Customer) -> list[dict]:
    sessions = list(ChatHistory.select().where(ChatHistory.user == user))
    return [_chat_history_to_dict(session) for session in sessions]


def get_chat_session(session_id: str, user: Customer) -> dict | None:
    session = ChatHistory.get_or_none(
        (ChatHistory.session_id == session_id) & (ChatHistory.user == user)
    )
    return _chat_history_to_dict(session) if session else None


def delete_chat_session(session_id: str, user: Customer) -> bool:
    deleted_count = (
        ChatHistory.delete()
        .where((ChatHistory.session_id == session_id) & (ChatHistory.user == user))
        .execute()
    )
    return deleted_count > 0


def init_db() -> None:
    database.connect(reuse_if_open=True)
    database.create_tables([Product, Customer, Order, ChatHistory])
    _migrate_api_credential_customer_column()
    database.create_tables([ApiCredential])
    _seed_default_api_credential()


init_db()

ECOMMERCE_DB = {
    "products": _TableView(Product, _product_to_dict),
    "customers": _TableView(Customer, _customer_to_dict),
    "orders": _TableView(Order, _order_to_dict, _order_from_dict),
}
