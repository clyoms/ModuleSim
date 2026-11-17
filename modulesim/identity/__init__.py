"""Identity (Mocked): one fixed demo student, no login.

Interface:
    current_student() -> Student

Real accounts and UCC sign-in are a Won't have for the prototype. In the
target design this component checks sign-in. Callers only ask for the
current student, so real login would change this file and the web
package's request handling, and nothing else.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Student:
    id: str
    name: str


DEMO_STUDENT = Student(id="demo-student", name="Demo Student")


class DemoIdentity:
    def current_student(self) -> Student:
        return DEMO_STUDENT


__all__ = ["DEMO_STUDENT", "DemoIdentity", "Student"]
