/**
 * Customers module: typed API client for the customer/user endpoints.
 */
import { apiFetch } from "./api-client";

export interface Customer {
  id: string;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface CreateCustomerPayload {
  name: string;
  email: string;
  password: string;
}

async function errorDetail(response: Response, fallback: string): Promise<string> {
  try {
    const data = await response.json();
    return data.detail || fallback;
  } catch {
    return fallback;
  }
}

export async function listCustomers(): Promise<Customer[]> {
  const response = await apiFetch("/auth/users");
  if (!response.ok) {
    throw new Error(await errorDetail(response, "Failed to fetch customers"));
  }
  return response.json();
}

export async function createCustomer(
  payload: CreateCustomerPayload
): Promise<Customer> {
  const response = await apiFetch("/auth/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await errorDetail(response, "Failed to create customer"));
  }
  const data = await response.json();
  return data.customer;
}

export async function deleteCustomer(customerId: string): Promise<void> {
  const response = await apiFetch(`/auth/users/${customerId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(await errorDetail(response, "Failed to delete customer"));
  }
}
