# Java / Spring Boot Standards

## When to load this file

Load this reference when working on:

- Any `.java` file in the repo
- Spring Boot services (3.x+)
- Spring Cloud microservices
- Java backend APIs, batch jobs, schedulers
- Anything with `pom.xml`, `build.gradle`, or `build.gradle.kts`
- JPA / Hibernate / Spring Data projects

Java is class-heavy by nature. For SOLID, dependency direction, and object modeling rules, also load `oop.md`. This file covers Spring-specific layout, idioms, and the modularity rules that keep services from rotting into mud.

## Baseline tooling

- **Java 21 LTS or newer.** Records, pattern matching, virtual threads. No Java 8. No Java 11.
  - Before scaffolding a new project, WebSearch "latest Java LTS release" and pick the newest LTS.
- **Spring Boot 3.x+** only. That means **Jakarta EE** namespaces (`jakarta.persistence.*`, not `javax.persistence.*`).
- **Maven OR Gradle.** Pick one and commit. No mixed builds.
  - Gradle: use the **version catalog** (`libs.versions.toml`) as your lockfile-equivalent. Pin versions there, reference them everywhere.
  - Maven: use `dependencyManagement` and a parent BOM. Pin versions in one place.
- **Lombok is grudgingly accepted.** Use it for `@RequiredArgsConstructor` and `@Slf4j`. Avoid `@Data` on entities. Records replace most of what Lombok used to be for.

## Project structure: organize by feature, not by layer

Wrong way (organize by type, the Java textbook trap):

```
src/main/java/com/company/app/
  controllers/   <- all controllers dumped here
  services/      <- all services dumped here
  repositories/  <- all repos dumped here
  entities/      <- all entities dumped here
```

This collapses the first time the team grows past two people. Every feature touches four packages. Reviews become impossible.

**Right way: package by feature/domain.** Each domain owns its controller, service, repo, entity, DTOs, mapper, exceptions, enums, constants.

```
src/main/java/com/company/app/
  Application.java                        # @SpringBootApplication entry point

  config/                                 # cross-cutting Spring config
    SecurityConfig.java
    DatabaseConfig.java
    WebConfig.java
    AppProperties.java                    # @ConfigurationProperties root

  shared/                                 # truly shared, used by 3+ features
    exception/
      GlobalExceptionHandler.java         # @RestControllerAdvice
      AppException.java                   # base custom exception
      ErrorResponse.java                  # record
      ErrorCode.java                      # enum in its own file
    dto/
      PagedResponse.java
    constants/
      HttpHeaders.java                    # constants in their own file
      CacheKeys.java

  users/                                  # one feature, one package
    UserController.java                   # @RestController, routes only
    UserService.java                      # @Service, business logic
    UserRepository.java                   # @Repository, JPA interface
    User.java                             # @Entity
    UserRole.java                         # enum in its own file
    UserStatus.java                       # enum in its own file
    UserConstants.java                    # feature-local constants
    dto/
      UserDto.java                        # response record
      CreateUserRequest.java              # request record
      UpdateUserRequest.java
    mapper/
      UserMapper.java                     # MapStruct
    exception/
      UserNotFoundException.java
      DuplicateEmailException.java

  orders/
    ...

src/main/resources/
  application.yml                         # single source of config
  application-dev.yml
  application-prod.yml
  db/migration/                           # Flyway, never auto-DDL in prod
    V1__init.sql
    V2__add_user_roles.sql
```

### Yash modularity rules (Java-specific)

1. **Every enum gets its own file.** `UserRole.java`, `OrderStatus.java`. Never nested as `public enum` inside an entity. Enums move across features as needs change; standalone files make that trivial.
2. **Constants get their own file per scope.** Feature-scoped constants in `UserConstants.java`. App-wide constants in `shared/constants/`. Never sprinkle `public static final` across random classes.
3. **One public class per file.** Java enforces this for top-level. Do not work around it with nested classes for things that should be siblings.
4. **Package by feature, not by type.** If `UserController` and `UserService` are in different top-level packages, the structure is wrong.
5. **`shared/` is for code used by 3+ features.** Two features sharing something is coincidence. Three is a pattern. Resist premature extraction.
6. **Records over POJOs.** Use `record` for DTOs, value objects, and anything immutable. Lombok `@Data` classes are obsolete for these.

## Layer responsibilities

**Controller (`@RestController`):**

- Map HTTP to method calls.
- Validate input with `@Valid` / `@Validated`.
- Never contain business logic. Never call repositories directly.
- Return `ResponseEntity<DtoType>` or the DTO directly with `@ResponseStatus`.

**Service (`@Service`):**

- All business logic lives here.
- Orchestrates repositories, publishes events, applies rules.
- Mark transactional boundaries with `@Transactional`.
- One service per domain aggregate. `UserService` does not touch orders.

**Repository (`@Repository`):**

- Data access only.
- Extend `JpaRepository<Entity, ID>` or define `@Query` methods.
- Never apply business rules inside a repo method.

**Entity (`@Entity`):**

- Represents a DB table.
- Never expose entities directly as API responses. Always map to a DTO.
- Keep entities free of business logic methods that touch other aggregates.

```java
// UserController.java - thin, no logic
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public UserDto getUser(@PathVariable UUID id) {
        return userService.findById(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserDto createUser(@Valid @RequestBody CreateUserRequest req) {
        return userService.create(req);
    }
}
```

## Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Classes | PascalCase | `UserService` |
| Methods, fields | camelCase | `findByEmail` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Enum values | SCREAMING_SNAKE_CASE | `ACTIVE`, `SOFT_DELETED` |
| Packages | lowercase, dot-separated | `com.company.users` |
| DB columns | snake_case via `@Column` | `created_at` |
| DTOs | suffix Request / Response / Dto | `CreateUserRequest`, `UserDto` |
| Test methods | `methodName_scenario_expectedOutcome` | `findById_userExists_returnsUser` |

## DTOs as records

Records are immutable, concise, and built for this:

```java
public record UserDto(
    UUID id,
    String email,
    String name,
    Instant createdAt
) {}

public record CreateUserRequest(
    @NotBlank @Email String email,
    @NotBlank @Size(min = 2, max = 100) String name,
    @NotBlank @Size(min = 8) String password
) {}
```

Never accept or return `@Entity` types across the HTTP boundary. Map with MapStruct or a hand-written mapper.

## Centralized config: `application.yml` + `@ConfigurationProperties`

No `@Value("${...}")` scattered across services. That is config-as-typos waiting to happen.

```yaml
# application.yml
app:
  jwt:
    secret: ${JWT_SECRET}
    expiration-minutes: 60
  rate-limit:
    requests-per-minute: 100
    burst: 20
```

```java
// AppProperties.java in config/
@ConfigurationProperties(prefix = "app")
@Validated
public record AppProperties(
    @Valid JwtProperties jwt,
    @Valid RateLimitProperties rateLimit
) {
    public record JwtProperties(
        @NotBlank String secret,
        @Positive int expirationMinutes
    ) {}

    public record RateLimitProperties(
        @Positive int requestsPerMinute,
        @Positive int burst
    ) {}
}
```

Inject `AppProperties` wherever you need config. One source. Typed. Validated at startup. Fail-fast if misconfigured.

Secrets come from environment variables only. `${JWT_SECRET}` resolves at boot. Never commit real secrets to `application.yml`.

## Exception handling: custom hierarchy + `@ControllerAdvice`

**Step 1.** Build a custom exception hierarchy rooted in a base type. Each carries an `ErrorCode` enum value so HTTP mapping is deterministic.

```java
// shared/exception/AppException.java
public abstract class AppException extends RuntimeException {
    private final ErrorCode code;

    protected AppException(ErrorCode code, String message) {
        super(message);
        this.code = code;
    }

    public ErrorCode getCode() { return code; }
}

// shared/exception/ErrorCode.java (own file)
public enum ErrorCode {
    USER_NOT_FOUND(404),
    DUPLICATE_EMAIL(409),
    VALIDATION_FAILED(400),
    UNAUTHORIZED(401),
    FORBIDDEN(403),
    INTERNAL(500);

    private final int httpStatus;
    ErrorCode(int httpStatus) { this.httpStatus = httpStatus; }
    public int httpStatus() { return httpStatus; }
}

// users/exception/UserNotFoundException.java
public class UserNotFoundException extends AppException {
    public UserNotFoundException(UUID id) {
        super(ErrorCode.USER_NOT_FOUND, "User not found: " + id);
    }
}
```

**Step 2.** Map exceptions to HTTP in one place with `@RestControllerAdvice`:

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(AppException.class)
    public ResponseEntity<ErrorResponse> handleApp(AppException ex) {
        log.warn("App exception: {}", ex.getMessage());
        return ResponseEntity
            .status(ex.getCode().httpStatus())
            .body(new ErrorResponse(ex.getCode().name(), ex.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex) {
        var errors = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> e.getField() + ": " + e.getDefaultMessage())
            .toList();
        return ResponseEntity.badRequest()
            .body(new ErrorResponse("VALIDATION_FAILED", "Validation failed", errors));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleUnknown(Exception ex) {
        log.error("Unhandled exception", ex);
        return ResponseEntity.internalServerError()
            .body(new ErrorResponse("INTERNAL", "Internal server error"));
    }
}
```

No `try / catch` in controllers. Let exceptions bubble. The advice owns HTTP mapping. Services throw domain exceptions; they do not know about HTTP status codes.

## Dependency injection: constructor only

**Never use field injection.** No `@Autowired` on fields. Field injection makes classes untestable without Spring and hides dependencies.

```java
// Good - constructor injection via Lombok
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
    private final AppProperties props;
}

// Bad - field injection
@Service
public class UserService {
    @Autowired private UserRepository userRepository;  // banned
    @Autowired private EmailService emailService;      // banned
}
```

If a class has more than 5 constructor dependencies, it is doing too much. Split it. That is SOLID telling you something. See `oop.md`.

## SOLID in Spring

Java is class-heavy. SOLID applies directly. Quick Spring-flavored summary; load `oop.md` for the full treatment.

- **S** Single Responsibility. One service per domain aggregate. `UserService` does not manage orders.
- **O** Open / Closed. Prefer strategy pattern over `if (type == X) ... else if (type == Y)` chains. Inject a `Map<String, PaymentStrategy>` and let Spring wire the implementations.
- **L** Liskov. Subtypes must honor the contract. Do not throw `UnsupportedOperationException` from an overridden method.
- **I** Interface Segregation. Small, focused interfaces. A `UserReader` and `UserWriter` may beat one fat `UserRepository` when you have CQRS-ish reads.
- **D** Dependency Inversion. Depend on interfaces. `@Profile` swaps implementations per environment (in-memory for tests, real client for prod).

## Database and migrations

- Flyway only. Auto-DDL (`spring.jpa.hibernate.ddl-auto=update`) is a footgun in any environment beyond a junior tutorial.
  - Local dev: `validate`.
  - Prod: `validate`.
  - Never `update` or `create-drop` against shared DBs.
- Migrations are immutable once merged. New change means new `V{N}__description.sql`.
- Use `UUID` primary keys for anything user-facing. Auto-increment `Long` is fine for purely internal tables.

## Testing

- **Unit tests:** `@ExtendWith(MockitoExtension.class)`. Mock every dependency. No Spring context loaded.
- **Integration tests:** `@SpringBootTest` with **Testcontainers** for a real Postgres / Redis / Kafka. No H2 pretending to be Postgres.
- **Test naming:** `methodName_scenario_expectedOutcome`. Example: `create_duplicateEmail_throwsDuplicateEmailException`.
- **AssertJ** for assertions, not JUnit's built-ins. `assertThat(user.email()).isEqualTo("...")`.
- Tests live next to the feature they test: `src/test/java/com/company/app/users/UserServiceTest.java`.

## What earns a PR rejection

- `@Autowired` on a field
- `@Entity` returned from a controller method
- Business logic inside a controller
- Business logic inside a repository method
- New `@Value("${...}")` instead of `@ConfigurationProperties`
- `try / catch` in a controller that swallows or re-maps to a status code
- Nested enum inside an entity for something more than a one-off marker
- New `org.springframework.boot` 2.x dependency added to a 3.x project
- `javax.*` imports in a Spring Boot 3 codebase
- `spring.jpa.hibernate.ddl-auto=update` committed to any non-throwaway profile
- A feature package missing one of: controller, service, repo, DTOs, mapper

## When this reference loads

This file loads automatically when the project shows Java fingerprints:

- A `pom.xml`, `build.gradle`, or `build.gradle.kts` at repo root
- Any `.java` file under `src/main/java/`
- An `application.yml` / `application.properties` under `src/main/resources/`
- A `@SpringBootApplication`-annotated class anywhere

When this loads, also load:

- `oop.md` for SOLID, composition over inheritance, dependency direction
- `testing.md` for the testing philosophy that underpins the unit / integration split above
- `security.md` for auth, secrets, and input validation rules that apply to every Spring controller

Java is verbose. The rules above exist so that verbosity buys clarity instead of noise. Package by feature. Inject by constructor. Map at the edges. Configure in one place. Let exceptions bubble. Everything else is detail.
