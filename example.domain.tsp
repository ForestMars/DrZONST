// example-domain.tsp
// Example domain model for testing etc.

import "@typespec/http";
import "@typespec/rest";

using TypeSpec.Http;
using TypeSpec.Rest;

namespace Example;

@doc("Represents a user in the system")
model User {

  @key
  @visibility
  id: string;

  @doc("Unique username for login")
  username: string;

  @doc("Email address for the user")
  email: string;

  @doc("User's first name")
  firstName?: string;

  @doc("User's last name")
  lastName?: string;

  @doc("Date of birth in YYYY-MM-DD format")
  dateOfBirth?: plainDate;

  @doc("Timestamp when user was created")
  createdAt: utcDateTime;

  @doc("Timestamp when user was last updated")
  updatedAt: utcDateTime;
}
