# proskills/models.py - Complete Updated File

from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string
import datetime
# jjj


# ============================================
# 1️⃣ USER MODEL - UPDATED
# ============================================
class User(AbstractUser):
    ROLE_CHOICES = (('admin', 'Admin'), ('franchise', 'Franchise'))
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='franchise')
    franchise_code = models.CharField(max_length=20, unique=True, null=True, blank=True, db_index=True)
    location = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.franchise_code and self.role == 'franchise':
            self.franchise_code = self.generate_franchise_code()
        super().save(*args, **kwargs)

    def generate_franchise_code(self):
        """Generate unique franchise code: FR-YYYY-XXXX"""
        return next_franchise_code()

    def __str__(self):
        return f"{self.username} ({self.role})"


# ============================================
# 2️⃣ CATEGORY MODEL
# ============================================
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# ============================================
# 3️⃣ SESSION MODEL
# ============================================
class Session(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# ============================================
# 4️⃣ COURSE MODEL
# ============================================
class Course(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    course_name = models.CharField(max_length=255)
    sessions = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='courses')
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    franchise = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses', 
                                  limit_choices_to={'role': 'franchise'}, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.course_name


# ============================================
# 5️⃣ JOB MODEL
# ============================================
class Job(models.Model):
    JOB_TYPES = (
        ('Government', 'Government'),
        ('Private', 'Private'),
    )
    
    job_title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='Private')
    category = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    experience_required = models.IntegerField(default=0)
    qualification = models.CharField(max_length=255, blank=True, null=True)
    application_deadline = models.DateField()
    job_link = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='posted_jobs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"


# ============================================
# 6️⃣ FRANCHISE PAYMENT MODEL
# ============================================
class FranchisePayment(models.Model):
    PAYMENT_STATUS = (
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
        ('Completed', 'Completed'),
    )
    
    PAYMENT_METHODS = (
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cheque', 'Cheque'),
        ('Card', 'Card'),
    )
    
    franchise_code = models.CharField(max_length=20)
    applicant_name = models.CharField(max_length=255)
    father_name = models.CharField(max_length=255, blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    institute_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash')
    payment_date = models.DateField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Pending')
    note = models.TextField(blank=True, null=True)
    payment_history = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.franchise_code} - {self.applicant_name} - {self.payment_status}"


# ============================================
# 7️⃣ STUDENT MODEL
# ============================================
class Student(models.Model):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
        ('Completed', 'Completed'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
    )

    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Completed', 'Completed'),
    )

    # ===== STUDENT BASIC DETAILS =====
    student_name = models.CharField(max_length=255)
    father_name = models.CharField(max_length=255)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    dob = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    # ===== CONTACT DETAILS =====
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    # ===== COURSE DETAILS =====
    course_category = models.CharField(max_length=100)
    course_name = models.CharField(max_length=255)
    sessions = models.CharField(max_length=100)

    # ===== FEE DETAILS =====
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ===== PAYMENT DETAILS =====
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='Pending'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True
    )

    # ===== 🔥 FRANCHISE FIELDS =====
    franchise_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True
    )
    franchise_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    created_by = models.CharField(max_length=100, blank=True, null=True)

    # ===== MEDIA & DOCUMENTS =====
    photo = models.TextField(blank=True, null=True)
    documents = models.JSONField(default=dict, blank=True)

    # ===== STATUS & DATES =====
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Active'
    )
    admitted_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'students'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['franchise_code']),
            models.Index(fields=['franchise_code', 'created_at']),
            models.Index(fields=['student_name']),
            models.Index(fields=['mobile']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.student_name} - {self.course_name} ({self.franchise_code or 'Admin'})"


# ============================================
# 8️⃣ PAYMENT MODEL
# ============================================
class Payment(models.Model):
    PAYMENT_STATUS = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    PAYMENT_METHODS = (
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
    )

    # ===== STUDENT REFERENCE =====
    student_id = models.IntegerField(null=True, blank=True)
    student_name = models.CharField(max_length=255)
    course_name = models.CharField(max_length=255)

    # ===== PAYMENT DETAILS =====
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Pending')
    receipt_no = models.CharField(max_length=50, unique=True, blank=True, null=True)

    # ===== 🔥 FRANCHISE FIELDS =====
    franchise_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True
    )
    franchise_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # ===== DATES =====
    payment_date = models.DateField(auto_now_add=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['franchise_code']),
            models.Index(fields=['franchise_code', 'created_at']),
            models.Index(fields=['receipt_no']),
            models.Index(fields=['student_name']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.student_name} - ₹{self.amount} - {self.status} ({self.franchise_code or 'Admin'})"

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            import time
            self.receipt_no = f"RCP-{int(time.time() * 1000) % 1000000:06d}"
        super().save(*args, **kwargs)


# ============================================
# 🔧 VOCATIONAL STUDENT MODEL
# ============================================
class VocationalStudent(models.Model):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
        ('Completed', 'Completed'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
    )
    
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Completed', 'Completed'),
    )

    # ===== STUDENT BASIC DETAILS =====
    student_name = models.CharField(max_length=255)
    father_name = models.CharField(max_length=255)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    dob = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    # ===== CONTACT DETAILS =====
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    # ===== COURSE DETAILS =====
    course_category = models.CharField(max_length=100)
    course_name = models.CharField(max_length=255)
    sessions = models.CharField(max_length=100)
    course_type = models.CharField(max_length=20, default='vocational')

    # ===== FEE DETAILS =====
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ===== PAYMENT DETAILS =====
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)

    # ===== 🔥 FRANCHISE FIELDS =====
    franchise_code = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    franchise_name = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)

    # ===== MEDIA & DOCUMENTS =====
    photo = models.TextField(blank=True, null=True)
    adhar_card = models.TextField(blank=True, null=True)
    marksheet_10 = models.TextField(blank=True, null=True)
    signature = models.TextField(blank=True, null=True)

    # ===== STATUS & DATES =====
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    admission_date = models.DateField(blank=True, null=True)

    # ✅ FIXED - null=True, blank=True added
    admitted_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'vocational_students'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['franchise_code']),
            models.Index(fields=['franchise_code', 'created_at']),
            models.Index(fields=['student_name']),
            models.Index(fields=['mobile']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return f"{self.student_name} - {self.course_name} ({self.franchise_code or 'Admin'})"

    def save(self, *args, **kwargs):
        import datetime
        if not self.admission_date:
            self.admission_date = datetime.date.today()
        super().save(*args, **kwargs)


# ============================================
# 💳 VOCATIONAL PAYMENT MODEL
# ============================================
class VocationalPayment(models.Model):
    PAYMENT_STATUS = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    PAYMENT_METHODS = (
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
    )

    # ===== STUDENT REFERENCE =====
    student_id = models.IntegerField(null=True, blank=True)
    student_name = models.CharField(max_length=255)
    course_name = models.CharField(max_length=255)

    # ===== PAYMENT DETAILS =====
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Completed')
    receipt_no = models.CharField(max_length=50, unique=True, blank=True, null=True)

    # ===== 🔥 FRANCHISE FIELDS =====
    franchise_code = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    franchise_name = models.CharField(max_length=255, blank=True, null=True)

    # ===== DATES =====
    payment_date = models.DateField(auto_now_add=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'vocational_payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['franchise_code']),
            models.Index(fields=['franchise_code', 'created_at']),
            models.Index(fields=['receipt_no']),
            models.Index(fields=['student_name']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.student_name} - ₹{self.amount} - {self.status} ({self.franchise_code or 'Admin'})"

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            import time
            self.receipt_no = f"VOC-{int(time.time() * 1000) % 1000000:06d}"
        super().save(*args, **kwargs)
        
# ============================================
# 1️⃣1️⃣ APPLICATION MODEL
# ============================================
class Application(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    
    name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    franchise_name = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    admin_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'applications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.status}"


# ============================================
# 1️⃣2️⃣ GENERATED FRANCHISE MODEL - UPDATED
# ============================================
class GeneratedFranchise(models.Model):
    STATUS_CHOICES = (
        ('Generated', 'Generated'),
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )
    
    request_id = models.IntegerField(null=True, blank=True)
    applicant_name = models.CharField(max_length=100)
    franchise_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    
    # 🔥 NEW: Franchise Code field
    franchise_code = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    
    agreement_date = models.DateField(null=True, blank=True)
    validity_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    selected_courses = models.JSONField(default=list, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Generated')
    
    # 🔥 NEW: Track if user created
    user_created = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'generated_franchises'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.applicant_name} - {self.franchise_name}"


# ============================================
# 1️⃣3️⃣ FRANCHISE MODEL - KEEP AS IS
# ============================================
class Franchise(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        db_table = 'franchises'
        ordering = ['-created_at']


# ============================================
# 1️⃣4️⃣ APPLICANT MODEL - KEEP AS IS
# ============================================
class Applicant(models.Model):
    franchise = models.ForeignKey(Franchise, on_delete=models.CASCADE, related_name='applicants')
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.franchise.name}"

    class Meta:
        db_table = 'applicants'
        ordering = ['-created_at']


# ============================================
# 1️⃣5️⃣ FRANCHISE USER MODEL - UPDATED
# ============================================
class FranchiseUser(models.Model):

 # 🔥 YAHAN ADD KAREIN: Expiry/Validity Date
    validity_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='franchise_user')
    franchise = models.ForeignKey(Franchise, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    generated_franchise = models.ForeignKey(GeneratedFranchise, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    
    # 🔥 NEW FIELDS
    franchise_code = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    franchise_name = models.CharField(max_length=200, null=True, blank=True)
    applicant_name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    permissions = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def generate_franchise_code():
        """Generate unique franchise code: FR-YYYY-XXXX"""
        return next_franchise_code()

    def save(self, *args, **kwargs):
        if not self.franchise_code:
            self.franchise_code = self.generate_franchise_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.franchise_name} ({self.franchise_code})"

    class Meta:
        db_table = 'franchise_users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['franchise_code']),
        ]


# ============================================
# 1️⃣6️⃣ USER PERMISSION MODEL - KEEP AS IS
# ============================================
class UserPermission(models.Model):
    PERMISSION_CHOICES = [
        ('dashboard', '🏠 Dashboard'),
        ('students', '👨‍🎓 Students'),
        ('student_admission', '📝 Student Admission'),
        ('student_report', '📊 Student Report'),
        ('payments', '💳 Payments'),
        ('payment_entry', '💰 Payment Entry'),
        ('payment_report', '📊 Payment Report'),
        ('certificates', '📜 Certificates'),
        ('certificate_generate', '🖨️ Generate Certificate'),
        ('certificate_report', '📊 Certificate Report'),
        ('vocational', '🔧 Vocational'),
        ('vocational_registration', '📝 Vocational Registration'),
        ('vocational_report', '📊 Vocational Report'),
        ('jobs', '💼 Jobs'),
        ('job_report', '📊 Job Report'),
        ('franchise_manage', '🏢 Franchise'),
        ('franchise_generate', '📄 Generate Franchise'),
        ('franchise_report', '📊 Franchise Report'),
        ('users', '👥 Users'),
        ('user_create', '👤 Create User'),
        ('user_permissions', '🔐 User Permissions'),
        ('courses', '📚 Courses'),
        ('course_add', '📝 Add Course'),
        ('course_report', '📊 Course Report'),
        ('reports', '📊 Reports'),
        ('analytics', '📈 Analytics'),
        ('settings', '⚙️ Settings'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permissions')
    permission_key = models.CharField(max_length=50, choices=PERMISSION_CHOICES)
    granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_permissions')

    class Meta:
        db_table = 'user_permissions'
        unique_together = ['user', 'permission_key']

    def __str__(self):
        return f"{self.user.username} - {self.get_permission_key_display()}: {self.granted}"


# ============================================
# 1️⃣7️⃣ FRANCHISE CERTIFICATE MODEL
# ============================================
class FranchiseCertificate(models.Model):
    cert_no = models.CharField(max_length=50, unique=True, blank=True)
    franchise_code = models.CharField(max_length=50, blank=True)
    applicant_name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200, blank=True)
    franchise_name = models.CharField(max_length=200)
    authorized_area = models.CharField(max_length=200, blank=True)
    selected_category = models.CharField(max_length=100, blank=True)
    course_name = models.CharField(max_length=200)
    validity_from = models.CharField(max_length=50, default='1st April 2026')
    validity_to = models.CharField(max_length=50, default='31st March 2027')
    city = models.CharField(max_length=100, default='ASOLA/SURGUJA')
    state = models.CharField(max_length=100, default='CHHATTISGARH')
    center_coordinator = models.CharField(max_length=100, default='Rahul Mishra')
    director = models.CharField(max_length=100, default='Mr. Ajay Kumar Gupta')
    company_name = models.CharField(max_length=200, default='EduSkillVision')
    reg_no = models.CharField(max_length=100, default='U80900CT2023PTC014511')
    website = models.CharField(max_length=100, default='eduskillvision.com')
    iso = models.CharField(max_length=100, default='ISO 9001:2015 Certified')
    head_office = models.CharField(max_length=255, default='Ambikapur, Surguja (C.G.) 497001')
    regional_office = models.CharField(max_length=255, default='Bilaspur, Chhattisgarh')
    phone = models.CharField(max_length=20, default='+91 91111 37575')
    email = models.EmailField(max_length=100, default='info@eduskillvision.com')
    applicant_photo = models.TextField(blank=True, null=True)
    qr_image = models.TextField(blank=True, null=True)
    social_links = models.JSONField(default=list, blank=True)
    
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Expired', 'Expired'),
        ('Generated', 'Generated'),
    )
    status = models.CharField(max_length=20, default='Active', choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'franchise_certificates'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.cert_no} - {self.applicant_name}"

    def save(self, *args, **kwargs):
        if not self.cert_no:
            count = FranchiseCertificate.objects.count() + 1
            year = 2026
            self.cert_no = f"ESV/FR/{year}/{str(count).zfill(4)}"
        super().save(*args, **kwargs)

from django.db import models
from django.utils import timezone


# ============================================
# 📜 STUDENT CERTIFICATE MODEL - UPDATED
# ============================================
class StudentCertificate(models.Model):

    STUDENT_TYPE_CHOICES = (
        ('student', 'Student'),
        ('vocational', 'Vocational'),
    )

    RELATION_CHOICES = (
        ('Son', 'Son'),
        ('Daughter', 'Daughter'),
        ('Wife', 'Wife'),
    )

    # ===== CERTIFICATE INFO =====
    cert_no = models.CharField(max_length=50, unique=True, blank=True)
    enroll_no = models.CharField(max_length=50, blank=True)

    # ===== STUDENT DETAILS =====
    student_name = models.CharField(max_length=200)
    relation = models.CharField(max_length=20, choices=RELATION_CHOICES, default='Son')
    father_name = models.CharField(max_length=200)
    course_name = models.CharField(max_length=200)

    # ===== CERTIFICATE DETAILS =====
    center_name = models.CharField(max_length=100, default='EduSkillVision')
    grade = models.CharField(max_length=10, default='A+')
    duration = models.CharField(max_length=50, default='3 Months')
    issue_date = models.CharField(max_length=50, blank=True)

    # ===== AUTHORITY DETAILS =====
    center_coordinator = models.CharField(max_length=100, default='Mr. Rahul Mishra')
    director = models.CharField(max_length=100, default='Mr. Ajay Kumar Gupta')

    # ===== COMPANY DETAILS =====
    company_name = models.CharField(max_length=200, default='EduSkillVision')
    reg_no = models.CharField(max_length=100, default='U80900CT2023PTC014511')
    website = models.CharField(max_length=100, default='eduskillvision.com')
    unit = models.CharField(
        max_length=255,
        default='A unit of EduSkillVision Education Pvt. Ltd.'
    )
    iso = models.CharField(max_length=100, default='ISO 9001:2015 Certified')
    head_office = models.CharField(
        max_length=255,
        default='Ambikapur, Surguja (C.G.) 497001'
    )
    regional_office = models.CharField(
        max_length=255,
        default='Behind Kamal Auto Agency, Dhamtari (C.G.) Pin 493671'
    )
    phone = models.CharField(max_length=20, default='+91 91111 37575')
    email = models.EmailField(max_length=100, default='info@eduskillvision.com')

    # ===== MEDIA =====
    student_photo = models.TextField(blank=True, null=True)
    qr_image = models.TextField(blank=True, null=True)

    # ===== REFERENCE =====
    student_id = models.IntegerField(null=True, blank=True)
    student_type = models.CharField(
        max_length=20,
        choices=STUDENT_TYPE_CHOICES,
        default='student'
    )

    # ===== 🔥 FRANCHISE FIELDS =====
    franchise_code = models.CharField(
        max_length=50, blank=True, null=True, db_index=True
    )
    franchise_name = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)

    # ============================================
    # 🆕 WALLET / DOWNLOAD TRACKING FIELDS
    # ============================================
    is_downloaded = models.BooleanField(
        default=False,
        help_text='True if PDF downloaded at least once'
    )
    downloaded_at = models.DateTimeField(
        null=True, blank=True,
        help_text='First download timestamp'
    )
    download_count = models.IntegerField(
        default=0,
        help_text='Total download attempts'
    )
    wallet_deducted = models.BooleanField(
        default=False,
        help_text='True if wallet balance already deducted'
    )

    # ===== TIMESTAMPS =====
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'student_certificates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['franchise_code']),
            models.Index(fields=['franchise_code', 'created_at']),
            models.Index(fields=['student_name']),
            models.Index(fields=['cert_no']),
            models.Index(fields=['student_type']),
            models.Index(fields=['is_downloaded']),        # 🆕
            models.Index(fields=['wallet_deducted']),      # 🆕
        ]

    def __str__(self):
        return f"{self.cert_no} - {self.student_name} ({self.franchise_code or 'Admin'})"

    def save(self, *args, **kwargs):
        if not self.cert_no:
            count = StudentCertificate.objects.count() + 1
            year = 2026
            prefix = 'VOC' if self.student_type == 'vocational' else 'ESV'
            self.cert_no = f"{prefix}/{year}/{str(count).zfill(3)}"
            self.enroll_no = f"{prefix}/ENR/{str(count).zfill(3)}"
        super().save(*args, **kwargs)

    def mark_downloaded(self):
        """Mark certificate as downloaded"""
        if not self.is_downloaded:
            self.is_downloaded = True
            self.downloaded_at = timezone.now()
        self.download_count += 1
        self.save(update_fields=['is_downloaded', 'downloaded_at', 'download_count'])
# ============================================
# 📂 COURSE CATEGORY MODEL
# ============================================
class CourseCategory(models.Model):
    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default="📚")
    gradient = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_categories'
        ordering = ['-created_at']

    def __str__(self):
        return self.label


# ============================================
# ⏱️ COURSE DURATION MODEL
# ============================================
class CourseDuration(models.Model):
    value = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_durations'
        ordering = ['-created_at']

    def __str__(self):
        return self.value


# ============================================
# 📚 WEBSITE COURSE MODEL
# ============================================
class WebsiteCourse(models.Model):
    name = models.CharField(max_length=255)

    # ✅ unique=False add kiya — duplicate slug error nahi aayega
    slug = models.SlugField(max_length=255, blank=True, null=True, unique=False)

    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE, related_name='website_courses')
    duration = models.ForeignKey(CourseDuration, on_delete=models.CASCADE, related_name='website_courses')
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)
    students = models.CharField(max_length=50, blank=True, null=True)
    image         = models.URLField(max_length=500, blank=True, null=True)
    is_professional = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    source_course = models.OneToOneField(
        'Course', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='website_course',
    )

    class Meta:
        db_table = 'website_courses'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            import time
            from django.utils.text import slugify
            # ✅ Timestamp add kiya — unique slug guarantee
            self.slug = f"{slugify(self.name)}-{int(time.time())}"
        super().save(*args, **kwargs)


# ============================================
# 📋 WEBSITE ENQUIRY MODEL
# ============================================
class WebsiteEnquiry(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('enrolled', 'Enrolled'),
        ('rejected', 'Rejected'),
    )
    student_name = models.CharField(max_length=200)
    course_name = models.CharField(max_length=200, blank=True, null=True)
    course = models.ForeignKey(WebsiteCourse, on_delete=models.SET_NULL, null=True, blank=True, related_name='enquiries')
    mobile = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'website_enquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student_name} - {self.course_name}"
# ****************************************
#     Wallet System - Course Based
# ****************************************

# ============================================
# 💰 CERTIFICATE WALLET MODEL
# ============================================
class CertificateWallet(models.Model):
    franchise_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )
    franchise_name = models.CharField(max_length=255, blank=True)
    total_certificates = models.IntegerField(default=0)
    used_certificates = models.IntegerField(default=0)
    remaining_certificates = models.IntegerField(default=0)
    total_amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'certificate_wallets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['franchise_code']),
        ]

    def __str__(self):
        return (
            f"💰 {self.franchise_code} | "
            f"Remaining: {self.remaining_certificates} | "
            f"Used: {self.used_certificates}"
        )

    @property
    def is_balance_available(self):
        return self.remaining_certificates > 0 and self.is_active

    def add_certificates(self, count, amount):
        self.total_certificates += count
        self.remaining_certificates += count
        self.total_amount_paid += amount
        self.save()

    def deduct_certificate(self):
        if self.remaining_certificates <= 0:
            raise ValueError('Insufficient certificate balance!')
        self.used_certificates += 1
        self.remaining_certificates -= 1
        self.save()

    def refund_certificate(self):
        if self.used_certificates > 0:
            self.used_certificates -= 1
            self.remaining_certificates += 1
            self.save()

    # ✅ NEW: Course wise balance
    def get_course_balance(self, course_name):
        """Ek course ka balance nikaalta hai"""
        recharges = self.transactions.filter(
            course_name__iexact=course_name,
            transaction_type__in=['purchase', 'admin_add']
        ).aggregate(
            total=models.Sum('certificate_count')
        )['total'] or 0

        deductions = self.transactions.filter(
            course_name__iexact=course_name,
            transaction_type='deduction'
        ).aggregate(
            total=models.Sum('certificate_count')
        )['total'] or 0

        return {
            'total': recharges,
            'used': deductions,
            'remaining': recharges - deductions,
        }


# ============================================
# 📚 CERTIFICATE PACKAGE MODEL (Course Based)
# ============================================
class CertificatePackage(models.Model):
    PACKAGE_STATUS = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )

    # ✅ Course Name (Gold/Silver ki jagah)
    name = models.CharField(max_length=100)
    course_name = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Course name like Tally, Python, Web Dev"
    )

    description = models.TextField(blank=True)
    certificate_count = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    per_certificate_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=PACKAGE_STATUS,
        default='active'
    )
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'certificate_packages'
        ordering = ['course_name', 'certificate_count']

    def __str__(self):
        return (
            f"📚 {self.course_name or self.name} | "
            f"{self.certificate_count} Certs | ₹{self.price}"
        )

    def save(self, *args, **kwargs):
        # Course name automatic set karo agar khali hai
        if not self.course_name and self.name:
            self.course_name = self.name

        # Per certificate price calculate
        if self.certificate_count and self.certificate_count > 0:
            self.per_certificate_price = (
                self.price / self.certificate_count
            )
        super().save(*args, **kwargs)


# ============================================
# 🧾 WALLET TRANSACTION MODEL (Course Based)
# ============================================
class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('purchase', 'Package Purchase'),
        ('deduction', 'Certificate Generated'),
        ('refund', 'Certificate Deleted - Refund'),
        ('admin_add', 'Admin Added'),
        ('admin_remove', 'Admin Removed'),
    )

    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    PAYMENT_METHODS = (
        ('online', 'Online Payment'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('razorpay', 'Razorpay'),
        ('admin', 'Admin Adjustment'),
    )

    # ===== REFERENCES =====
    wallet = models.ForeignKey(
        CertificateWallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    package = models.ForeignKey(
        CertificatePackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    certificate = models.ForeignKey(
        StudentCertificate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # ===== TRANSACTION DETAILS =====
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    franchise_code = models.CharField(
        max_length=50,
        db_index=True
    )

    # ✅ NEW: Course name
    course_name = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Course name for this transaction"
    )

    certificate_count = models.IntegerField(default=0)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # ===== BALANCE SNAPSHOT =====
    balance_before = models.IntegerField(default=0)
    balance_after = models.IntegerField(default=0)

    # ===== PAYMENT =====
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='admin'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='completed'
    )
    payment_reference = models.CharField(
        max_length=100,
        blank=True
    )

    # ===== RAZORPAY FIELDS (rakh diya, delete mat karo) =====
    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # ===== META =====
    remarks = models.TextField(blank=True)
    created_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallet_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['franchise_code']),
            models.Index(fields=['course_name']),
            models.Index(fields=['franchise_code', 'course_name']),
            models.Index(fields=['franchise_code', 'created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['payment_status']),
        ]

    def __str__(self):
        return (
            f"🧾 {self.transaction_type} | "
            f"{self.franchise_code} | "
            f"📚 {self.course_name or 'N/A'} | "
            f"Count: {self.certificate_count} | "
            f"₹{self.amount}"
        )


def next_franchise_code():
    """Next FR-YYYY-XXXX code: highest existing numeric suffix + 1 across every
    table that stores franchise codes, so deletions or orphan rows can never collide."""
    year = datetime.datetime.now().year
    prefix = f'FR-{year}-'
    highest = 0
    for model, field in (
        (User, 'franchise_code'),
        (FranchiseUser, 'franchise_code'),
        (Franchise, 'code'),
        (GeneratedFranchise, 'franchise_code'),
    ):
        for code in model.objects.filter(
            **{f'{field}__startswith': prefix}
        ).values_list(field, flat=True):
            suffix = code[len(prefix):]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return f'{prefix}{str(highest + 1).zfill(4)}'
