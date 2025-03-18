// example-domain.tsp
// Example domain model for testing etc.

// example-domain.tsp
import "@typespec/http";
import "@typespec/rest";
import "@typespec/openapi";

using TypeSpec.Http;
using TypeSpec.Rest;
using TypeSpec.OpenAPI;

// Define service with just a title, removing deprecated version
@service(#{title: "User Management Service"})
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

@route("/users")
interface Users {
  @post
  @doc("Creates a new user")
  create(@body user: User): {
    @statusCode statusCode: 201;
    @body createdUser: User;
  } | {
    @statusCode statusCode: 400;
    @body error: ErrorResponse;
  };

  @get
  @route("/{id}")
  @doc("Gets a user by ID")
  get(@path id: string): User | {
    @statusCode statusCode: 404;
    @body error: ErrorResponse;
  };

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

  @delete
  @route("/{id}")
  @doc("Deletes a user")
  delete(@path id: string): {
    @statusCode statusCode: 204;
  } | {
    @statusCode statusCode: 404;
    @body error: ErrorResponse;
  };

  @get
  @doc("Lists all users")
  list(): User[];
}

model ErrorResponse {
  @doc("Error message")
  message: string;
  
  @doc("Error code")
  code?: string;
}