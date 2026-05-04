from django.test import TestCase
from .models import Student

class StudentModelTest(TestCase):

    def test_student_creation(self):
        student = Student.objects.create(
            registration_number="REG-001",
            name="Mirza",
            age=20,
            email="mirza@example.com",
            class_name="BSCS",
            course="Python"
        )

        self.assertEqual(student.name, "Mirza")
        self.assertEqual(student.registration_number, "REG-001")
