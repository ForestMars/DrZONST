// example-domain.tsp
// Example domain model for testing etc.

import "@typespec/http";
import "@typespec/rest";
import "@typespec/openapi";

using TypeSpec.Http;
using TypeSpec.Rest;
using TypeSpec.OpenAPI;

@service({
  title: "User Management Service",
  version: "1.0.0"
})
@route("/api")
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

// Resource interface for User operations
@route("/users")
interface Users {
  // Create a new user (POST)
  @post
  @doc("Creates a new user")
  create(@body user: User): {
    @statusCode statusCode: 201;
    @body createdUser: User;
  } | {
    @statusCode statusCode: 400;
    @body error: ErrorResponse;
  };

  // Read a user by ID (GET)
  @get
  @route("/{id}")
  @doc("Gets a user by ID")
  get(@path id: string): User | {
    @statusCode statusCode: 404;
    @body error: ErrorResponse;
  };

  // Update a user (PUT)
  @put
  @route("/{id}")
  @doc("Updates an existing user")
  update(
    @path id: string,
    @body user: User
  ): User | {
    @statusCode statusCode: 404;
    @body error: ErrorResponse;
  };

  // Delete a user (DELETE)
  @delete
  @route("/{id}")
  @doc("Deletes a user")
  delete(@path id: string): {
    @statusCode statusCode: 204;
  } | {
    @statusCode statusCode: 404;
    @body error: ErrorResponse;
  };

  // List all users (GET)
  @get
  @doc("Lists all users")
  list(): User[];
}

// Basic error response model
model ErrorResponse {
  @doc("Error message")
  message: string;
  
  @doc("Error code")
  code?: string;
}
