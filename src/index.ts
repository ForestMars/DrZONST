import { db } from "./db/client";
import { users } from "./db/schemas/users";

const main = async () => {
  console.log("Starting application...");
  
  // Example DB query
  const allUsers = await db.select().from(users);
  console.log("Users:", allUsers);
};

main().catch(console.error);
