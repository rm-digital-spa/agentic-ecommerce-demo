// Simple streaming client to invoke the local agent endpoint.
async function sendRequest(propmt: string, userEmail: string) {
  const res = await fetch("http://localhost:8000/invoke", {
    method: "POST",
    body: JSON.stringify({ query: propmt }),
    headers: {
      "Content-Type": "application/json",
      "User-Email": userEmail,
    },
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    // Each chunk is "data: {...}\n\n"
    // console.log(chunk);
    process.stdout.write(chunk);
  }
}
const propmt = process.argv[2];
const userEmail = process.argv[3];
// console.log(process.args)

if(!propmt) {
  throw new Error("Please provide a prompt as a command line argument");
}

if(!userEmail) {
  throw new Error("Please provide a user email as the second command line argument");
}

sendRequest(propmt, userEmail);
