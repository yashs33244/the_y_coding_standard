# Object-Oriented Design

Core engineering reference: OOP fundamentals, SOLID, clean-code principles, and relationship types with concrete examples. Apply consistently across TypeScript, Python, Java, and any class-based codebase in scope of the_y_coding_standard.

This file is loaded by the skill whenever the user is writing or reviewing class-based code, refactoring a domain model, designing a service layer, or asking about SOLID, design patterns, inheritance, composition, or any OOP topic.

## 1. Four Pillars of OOP

### 1.1 Abstraction

What it is: focus on what an object does, not how. Hide complex details. Expose only essential behavior.

How it looks: public methods define the contract; internals are private or hidden.

```ts
// Abstraction: caller uses start() and stop() without knowing engine details
class Car {
  private engine: Engine;

  start(): void {
    this.engine.ignite();
  }
  stop(): void {
    this.engine.shutOff();
  }
}
```

Types of abstraction:

- Data abstraction: hide how data is stored (use getters instead of raw fields).
- Control abstraction: hide how a process is implemented (`save()` instead of `open/write/close`).

```ts
// Data abstraction: storage details hidden
class UserRepo {
  private store: Map<string, User>;
  getById(id: string): User | undefined {
    return this.store.get(id);
  }
}
```

### 1.2 Encapsulation

What it is: bundle data and the methods that act on that data into one unit (a class). Restrict direct access to internal state to avoid accidental misuse.

How it looks: private fields, public accessors or methods. No direct property access from outside.

```ts
// Encapsulation: balance is protected; changes only through deposit / withdraw
class BankAccount {
  private balance: number = 0;

  deposit(amount: number): void {
    if (amount > 0) this.balance += amount;
  }
  withdraw(amount: number): boolean {
    if (amount > 0 && amount <= this.balance) {
      this.balance -= amount;
      return true;
    }
    return false;
  }
  getBalance(): number {
    return this.balance;
  }
}
```

### 1.3 Inheritance

What it is: a child class gets properties and behavior from a parent class to reuse code and model "is-a" relationships.

How it looks: child extends parent and can override methods or add new ones.

```ts
// Inheritance: SportsCar is-a Vehicle with extra behavior
class Vehicle {
  move(): void {
    console.log("Moving");
  }
}
class SportsCar extends Vehicle {
  turboBoost(): void {
    console.log("Turbo engaged");
  }
}
```

Inheritance warning: prefer composition unless an "is-a" relationship is genuine and stable. See section 3.

### 1.4 Polymorphism

What it is: different classes can be used through the same interface; the same method name behaves differently per type.

How it looks: parent reference, child instances, overridden methods or shared interface.

```ts
// Polymorphism: same call, different behavior per type
abstract class Shape {
  abstract draw(): void;
}
class Circle extends Shape {
  draw(): void {
    console.log("Drawing circle");
  }
}
class Square extends Shape {
  draw(): void {
    console.log("Drawing square");
  }
}
function render(s: Shape): void {
  s.draw();
}
render(new Circle());
render(new Square());
```

## 2. SOLID Principles

### 2.1 Single Responsibility Principle (SRP)

What it is: a class should have only one reason to change. One responsibility.

How it looks: one class does one job. Split reporting, persistence, and validation into separate types.

```ts
// SRP: each class has one job
class Order {
  constructor(
    public id: string,
    public total: number,
  ) {}
}
class OrderRepository {
  save(order: Order): void {
    // persist only
  }
}
class OrderReport {
  format(order: Order): string {
    return `Order ${order.id}: ${order.total}`;
  }
}
```

Yash rule: if you cannot describe a class in one sentence without using the word "and", it has more than one responsibility. Split it.

### 2.2 Open / Closed Principle (OCP)

What it is: open for extension, closed for modification. Add behavior via new code (a new class), not by editing existing code.

How it looks: use abstractions and new implementations instead of growing if / else chains inside existing classes.

```ts
// OCP: extend via new class, not by changing Discount
interface Discount {
  apply(amount: number): number;
}
class PercentDiscount implements Discount {
  constructor(private percent: number) {}
  apply(amount: number): number {
    return amount * (1 - this.percent / 100);
  }
}
class FixedDiscount implements Discount {
  constructor(private fixed: number) {}
  apply(amount: number): number {
    return Math.max(0, amount - this.fixed);
  }
}
```

Smell to catch in review: every time a new discount type forces an `if (type === "X")` branch inside the discount engine, OCP is broken.

### 2.3 Liskov Substitution Principle (LSP)

What it is: subclasses must be substitutable for their base class without breaking callers.

How it looks: overrides preserve contracts (same preconditions, same postconditions). No throwing new errors. No weakening guarantees.

```ts
// LSP: Rectangle can replace Shape without breaking callers
class Shape {
  area(): number {
    return 0;
  }
}
class Rectangle extends Shape {
  constructor(
    private w: number,
    private h: number,
  ) {
    super();
  }
  area(): number {
    return this.w * this.h;
  }
}
function printArea(s: Shape): void {
  console.log(s.area());
}
printArea(new Rectangle(3, 4));
```

Classic violation: `Square extends Rectangle` then overrides `setWidth` to also set height. Callers that expect independent width and height break.

### 2.4 Interface Segregation Principle (ISP)

What it is: clients should not depend on methods they do not use. Prefer small, focused interfaces.

How it looks: many small interfaces instead of one large one. Classes implement only what they need.

```ts
// ISP: split a fat interface into small ones
interface Readable {
  read(): string;
}
interface Writable {
  write(data: string): void;
}
class FileReader implements Readable {
  read(): string {
    return "data";
  }
}
class FileWriter implements Writable {
  write(data: string): void {}
}
// Client that only reads depends only on Readable
function consume(r: Readable): void {
  r.read();
}
```

### 2.5 Dependency Inversion Principle (DIP)

What it is: depend on abstractions (interfaces), not concrete classes. High-level logic should not import low-level details.

How it looks: inject interfaces. Concrete implementations passed in or provided by a composition root.

```ts
// DIP: OrderService depends on abstraction, not on a concrete Logger
interface Logger {
  log(msg: string): void;
}
class OrderService {
  constructor(private logger: Logger) {}
  placeOrder(): void {
    this.logger.log("Order placed");
  }
}
class ConsoleLogger implements Logger {
  log(msg: string): void {
    console.log(msg);
  }
}
const service = new OrderService(new ConsoleLogger());
```

Yash rule: every service class accepts its dependencies through the constructor. No service news up its own logger, db client, or HTTP client.

## 3. Composition Over Inheritance

What it is: favor composing objects (has-a) over deep inheritance (is-a) to reduce coupling and increase flexibility.

How it looks: classes hold references to other types instead of extending them. Behavior is delegated.

```ts
// Composition: Engine is a component, not a parent
class Engine {
  start(): void {
    console.log("Engine started");
  }
}
class Car {
  private engine: Engine;
  constructor() {
    this.engine = new Engine();
  }
  start(): void {
    this.engine.start();
  }
}
```

When to use inheritance: only when the "is-a" relationship is genuine, stable, and shared behavior is large. For everything else, compose.

Yash rule: any inheritance hierarchy deeper than two levels is a smell. Refactor toward composition.

## 4. Clean Code Principles

### 4.1 DRY (Don't Repeat Yourself)

What it is: avoid duplicating logic. Centralize in one place.

```ts
// DRY: single function for validation
function isValidEmail(s: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
}
// Reuse everywhere instead of copying the regex
```

Yash rule: abstract on the 3rd occurrence, not the 2nd. Two similar lines may diverge. Three is a pattern.

### 4.2 KISS (Keep It Simple, Stupid)

What it is: avoid unnecessary complexity. Prefer straightforward solutions.

```ts
// KISS: simple condition instead of an over-engineered pattern
function isEligible(age: number): boolean {
  return age >= 18;
}
```

### 4.3 YAGNI (You Aren't Gonna Need It)

What it is: do not add functionality until it is required.

How it looks: no speculative features, no "might need later" code, no abstraction without two concrete cases that prove it. Implement when the need exists.

Yash rule: the cost of a wrong abstraction is greater than the cost of duplication.

### 4.4 Law of Demeter (LoD)

What it is: an object should only talk to its immediate neighbors (its own attributes, method arguments, or objects it creates). Avoid long chains like `a.getB().getC().doSomething()`.

How it looks: delegate to a neighbor so the caller uses one dot.

```ts
// LoD violation: client knows internal structure
// client.getAddress().getStreet().toUpperCase()

// Better: one level of indirection
class Client {
  private address: Address;
  getStreetUpperCase(): string {
    return this.address.getStreet().toUpperCase();
  }
}
```

Heuristic: every `.` in a method chain is a dependency. Two dots is a smell. Three is a violation.

## 5. Advanced Relationship Types

### 5.1 Association

What it is: general link between two objects. They can interact but are not necessarily owned.

```ts
// Association: Teacher and Student know each other
class Teacher {
  constructor(public students: Student[]) {}
}
class Student {
  constructor(public teacher: Teacher) {}
}
```

### 5.2 Aggregation (has-a, child can outlive parent)

What it is: whole has parts. Parts can exist without the whole (e.g. a department has employees; employees can exist without the department).

```ts
// Aggregation: Department has Employees; employees can exist independently
class Department {
  constructor(public employees: Employee[] = []) {}
  add(e: Employee): void {
    this.employees.push(e);
  }
}
class Employee {
  constructor(public name: string) {}
}
```

### 5.3 Composition (part-of, child cannot outlive parent)

What it is: strong ownership. The part does not exist without the whole (e.g. an engine cannot exist without the car in the same lifecycle).

```ts
// Composition: Engine is created and owned by Car; lifecycles are bound
class Car {
  private engine: Engine;
  constructor() {
    this.engine = new Engine();
  }
}
class Engine {}
```

## 6. Python Mapping (because Yash standards default to Python + TS)

The principles are identical. Syntax differs.

```python
# DIP in Python: depend on an abstraction
from typing import Protocol

class Logger(Protocol):
    def log(self, msg: str) -> None: ...

class OrderService:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def place_order(self) -> None:
        self._logger.log("Order placed")

class ConsoleLogger:
    def log(self, msg: str) -> None:
        print(msg)

service = OrderService(ConsoleLogger())
```

Python notes:
- Use `Protocol` for interface segregation. Duck typing plus static checks via `mypy --strict`.
- Use `@dataclass(frozen=True, slots=True)` for value objects.
- Use `abc.ABC` and `@abstractmethod` for true abstract base classes when subclasses must implement a method.
- Composition via constructor injection. Never default-construct collaborators inside a service.

## 7. Review Checklist (use during /y-review or any code review)

Quick checks to run against any class-heavy diff:

- [ ] Each class has one responsibility describable in one sentence.
- [ ] Inheritance depth is at most two.
- [ ] No fat interfaces. Each interface has at most 5 methods unless justified.
- [ ] No service constructs its own dependencies (logger, db, http client).
- [ ] Public methods preserve LSP. Overrides don't throw new exceptions or tighten preconditions.
- [ ] No long chains (`a.b.c.d`). LoD respected.
- [ ] No premature abstraction. YAGNI honored.
- [ ] DRY applied at the 3rd occurrence, not the 2nd.
- [ ] No `if (type === "X")` branches that should be polymorphism.
- [ ] No mutable global state.
- [ ] No public mutable fields. Encapsulation honored.

## 8. Quick Reference

| Concept | One-line |
|---|---|
| Abstraction | Expose what, hide how |
| Encapsulation | Bundle data + methods, restrict direct access |
| Inheritance | Child reuses parent behavior (is-a) |
| Polymorphism | Same interface, different behavior per type |
| SRP | One reason to change per class |
| OCP | Extend via new code, don't modify existing |
| LSP | Subtypes substitutable for base type |
| ISP | Small interfaces, no unused methods |
| DIP | Depend on abstractions, not concretions |
| Composition | Prefer has-a over deep inheritance |
| DRY | One place for each piece of logic |
| KISS | Prefer simple design |
| YAGNI | Build only what is needed now |
| LoD | Talk only to immediate neighbors |
| Association | General link between objects |
| Aggregation | Has-a, part can outlive whole |
| Composition (rel) | Part-of, part bound to whole lifecycle |

## 9. When this reference loads

This reference loads when the skill detects any of:

- The user is designing or refactoring classes.
- The diff or file under review contains class definitions.
- The user mentions SOLID, OOP, design patterns, inheritance, composition, polymorphism, encapsulation, abstraction, DRY, KISS, YAGNI, LoD, Demeter, dependency injection, or any of the relationship types (association, aggregation, composition).
- The user asks "is this class clean", "is this SRP-compliant", "should I extend or compose", or any class-design question.

When loaded, apply the rules silently while writing code. Surface them only during reviews or when the user explicitly asks why a structure was chosen.
