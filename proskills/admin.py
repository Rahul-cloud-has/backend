# proskills/admin.py - COMPLETE UPDATED FILE
# jj
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Category, Session, Course, Job, FranchisePayment, 
    Student, Payment, VocationalStudent, VocationalPayment,
    Application, GeneratedFranchise, Franchise, Applicant, 
    FranchiseUser, UserPermission, FranchiseCertificate, 
    StudentCertificate, CourseCategory, CourseDuration, WebsiteCourse, WebsiteEnquiry,
    CertificateWallet,      # 🆕
    CertificatePackage,     # 🆕
    WalletTransaction,      # 🆕

)


# ============================================
# 1️⃣ USER ADMIN
# ============================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['id', 'username', 'email', 'role', 'franchise_code', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'email', 'franchise_code']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('role', 'franchise_code', 'location', 'phone', 'is_active')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )


# ============================================
# 2️⃣ CATEGORY ADMIN
# ============================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']


# ============================================
# 3️⃣ SESSION ADMIN
# ============================================
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']


# ============================================
# 4️⃣ COURSE ADMIN
# ============================================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['id', 'course_name', 'category', 'sessions', 'fee', 'franchise', 'is_active']
    list_filter = ['category', 'sessions', 'is_active']
    search_fields = ['course_name']


# ============================================
# 5️⃣ JOB ADMIN
# ============================================
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['id', 'job_title', 'company_name', 'job_type', 'category', 'location', 'is_active', 'created_at']
    list_filter = ['job_type', 'category', 'is_active']
    search_fields = ['job_title', 'company_name', 'category']


# ============================================
# 6️⃣ FRANCHISE PAYMENT ADMIN
# ============================================
@admin.register(FranchisePayment)
class FranchisePaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'franchise_code', 'applicant_name', 
        'total_amount', 'paid_amount', 'due_amount', 
        'payment_status', 'payment_method', 'created_at'
    ]
    list_filter = ['payment_status', 'payment_method']
    search_fields = ['franchise_code', 'applicant_name', 'mobile']
    readonly_fields = ['created_at', 'updated_at']


# ============================================
# 7️⃣ STUDENT ADMIN
# ============================================
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'student_name', 'father_name', 'mobile',
        'course_name', 'course_category', 'fee_amount',
        'payment_status', 'franchise_code', 'status', 'created_at'
    ]
    list_filter = [
        'payment_status', 'course_category',
        'status', 'gender', 'created_at'
    ]
    search_fields = [
        'student_name', 'father_name', 'mobile',
        'email', 'franchise_code', 'course_name'
    ]
    readonly_fields = ['admitted_at', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('👤 Student Basic Details', {
            'fields': (
                'student_name', 'father_name', 'mother_name',
                'dob', 'gender'
            )
        }),
        ('📞 Contact Details', {
            'fields': (
                'mobile', 'email', 'address',
                'city', 'state', 'pincode'
            )
        }),
        ('📚 Course Details', {
            'fields': (
                'course_category', 'course_name', 'sessions'
            )
        }),
        ('💰 Fee & Payment', {
            'fields': (
                'fee_amount', 'total_payment',
                'payment_status', 'payment_method'
            )
        }),
        ('🔥 Franchise Info', {
            'fields': (
                'franchise_code', 'franchise_name', 'created_by'
            )
        }),
        ('📸 Media', {
            'fields': ('photo', 'documents')
        }),
        ('📊 Status & Dates', {
            'fields': (
                'status', 'admitted_at',
                'created_at', 'updated_at'
            )
        }),
    )

    actions = ['mark_active', 'mark_inactive', 'mark_completed']

    def mark_active(self, request, queryset):
        updated = queryset.update(status='Active')
        self.message_user(request, f'✅ {updated} student(s) marked Active.')
    mark_active.short_description = '✅ Mark as Active'

    def mark_inactive(self, request, queryset):
        updated = queryset.update(status='Inactive')
        self.message_user(request, f'❌ {updated} student(s) marked Inactive.')
    mark_inactive.short_description = '❌ Mark as Inactive'

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='Completed')
        self.message_user(request, f'🎓 {updated} student(s) marked Completed.')
    mark_completed.short_description = '🎓 Mark as Completed'


# ============================================
# 8️⃣ PAYMENT ADMIN
# ============================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'receipt_no', 'student_name', 'course_name',
        'amount', 'method', 'status',
        'franchise_code', 'payment_date', 'created_at'
    ]
    list_filter = [
        'status', 'method',
        'payment_date', 'created_at'
    ]
    search_fields = [
        'student_name', 'course_name',
        'receipt_no', 'franchise_code'
    ]
    readonly_fields = ['payment_date', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('👤 Student Reference', {
            'fields': ('student_id', 'student_name', 'course_name')
        }),
        ('💳 Payment Details', {
            'fields': ('amount', 'method', 'status', 'receipt_no')
        }),
        ('🔥 Franchise Info', {
            'fields': ('franchise_code', 'franchise_name')
        }),
        ('🕐 Timestamps', {
            'fields': ('payment_date', 'created_at', 'updated_at')
        }),
    )

    actions = ['mark_completed', 'mark_pending', 'mark_failed']

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='Completed')
        self.message_user(request, f'✅ {updated} payment(s) marked Completed.')
    mark_completed.short_description = '✅ Mark as Completed'

    def mark_pending(self, request, queryset):
        updated = queryset.update(status='Pending')
        self.message_user(request, f'⏳ {updated} payment(s) marked Pending.')
    mark_pending.short_description = '⏳ Mark as Pending'

    def mark_failed(self, request, queryset):
        updated = queryset.update(status='Failed')
        self.message_user(request, f'❌ {updated} payment(s) marked Failed.')
    mark_failed.short_description = '❌ Mark as Failed'

# ============================================
# 9️⃣ VOCATIONAL STUDENT ADMIN
# ============================================
@admin.register(VocationalStudent)
class VocationalStudentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'student_name', 'mobile', 'course_name',
        'course_category', 'fee_amount', 'payment_status',
        'franchise_code', 'admission_date', 'status'
    ]
    list_filter = [
        'course_category', 'payment_status',
        'status', 'gender', 'admission_date'
    ]
    search_fields = [
        'student_name', 'mobile', 'email',
        'course_name', 'franchise_code'
    ]
    readonly_fields = ['created_at', 'updated_at', 'admitted_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Student Basic Details', {
            'fields': (
                'student_name', 'father_name', 'mother_name',
                'dob', 'gender'
            )
        }),
        ('Contact Details', {
            'fields': (
                'mobile', 'email', 'address',
                'city', 'state', 'pincode'
            )
        }),
        ('Course Details', {
            'fields': (
                'course_category', 'course_name',
                'sessions', 'course_type'
            )
        }),
        ('Fee & Payment', {
            'fields': (
                'fee_amount', 'total_payment',
                'payment_status', 'payment_method'
            )
        }),
        ('Franchise Info', {
            'fields': (
                'franchise_code', 'franchise_name', 'created_by'
            )
        }),
        ('Documents', {
            'fields': (
                'photo', 'adhar_card',
                'marksheet_10', 'signature'
            )
        }),
        ('Status & Dates', {
            'fields': (
                'status', 'admission_date'
            )
        }),
        ('Timestamps', {
            'fields': ('admitted_at', 'created_at', 'updated_at')
        }),
    )

    actions = ['mark_active', 'mark_inactive', 'mark_completed']

    def mark_active(self, request, queryset):
        updated = queryset.update(status='Active')
        self.message_user(request, f'✅ {updated} student(s) marked Active.')
    mark_active.short_description = '✅ Mark as Active'

    def mark_inactive(self, request, queryset):
        updated = queryset.update(status='Inactive')
        self.message_user(request, f'❌ {updated} student(s) marked Inactive.')
    mark_inactive.short_description = '❌ Mark as Inactive'

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='Completed')
        self.message_user(request, f'🎓 {updated} student(s) marked Completed.')
    mark_completed.short_description = '🎓 Mark as Completed'


# ============================================
# 🔟 VOCATIONAL PAYMENT ADMIN
# ============================================
@admin.register(VocationalPayment)
class VocationalPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'receipt_no', 'student_name', 'course_name',
        'amount', 'method', 'status',
        'franchise_code', 'payment_date'
    ]
    list_filter = ['method', 'status', 'payment_date']
    search_fields = [
        'receipt_no', 'student_name',
        'course_name', 'franchise_code'
    ]
    readonly_fields = ['created_at', 'updated_at', 'payment_date']
    ordering = ['-created_at']

    fieldsets = (
        ('Student Reference', {
            'fields': ('student_id', 'student_name', 'course_name')
        }),
        ('Payment Details', {
            'fields': ('amount', 'method', 'status', 'receipt_no')
        }),
        ('Franchise Info', {
            'fields': ('franchise_code', 'franchise_name')
        }),
        ('Timestamps', {
            'fields': ('payment_date', 'created_at', 'updated_at')
        }),
    )

    actions = ['mark_completed', 'mark_pending', 'mark_failed']

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='Completed')
        self.message_user(request, f'✅ {updated} payment(s) marked Completed.')
    mark_completed.short_description = '✅ Mark as Completed'

    def mark_pending(self, request, queryset):
        updated = queryset.update(status='Pending')
        self.message_user(request, f'⏳ {updated} payment(s) marked Pending.')
    mark_pending.short_description = '⏳ Mark as Pending'

    def mark_failed(self, request, queryset):
        updated = queryset.update(status='Failed')
        self.message_user(request, f'❌ {updated} payment(s) marked Failed.')
    mark_failed.short_description = '❌ Mark as Failed'

# ============================================
# 1️⃣1️⃣ APPLICATION ADMIN
# ============================================
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'mobile', 'email', 'franchise_name', 'status', 'created_at']
    list_filter = ['status', 'city', 'state']
    search_fields = ['name', 'mobile', 'email', 'franchise_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'father_name', 'mobile', 'email')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Franchise Details', {
            'fields': ('franchise_name', 'message')
        }),
        ('Status & Notes', {
            'fields': ('status', 'admin_note')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['approve_applications', 'reject_applications']
    
    def approve_applications(self, request, queryset):
        updated = queryset.update(status='Approved')
        self.message_user(request, f'✅ {updated} application(s) approved successfully.')
    approve_applications.short_description = '✅ Approve selected applications'
    
    def reject_applications(self, request, queryset):
        updated = queryset.update(status='Rejected')
        self.message_user(request, f'❌ {updated} application(s) rejected.')
    reject_applications.short_description = '❌ Reject selected applications'


# ============================================
# 1️⃣2️⃣ GENERATED FRANCHISE ADMIN
# ============================================
@admin.register(GeneratedFranchise)
class GeneratedFranchiseAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'applicant_name', 'franchise_name', 'mobile', 
        'total_amount', 'status', 'user_created', 'created_at'
    ]
    list_filter = ['status', 'city', 'state', 'user_created']
    search_fields = ['applicant_name', 'franchise_name', 'mobile', 'email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Applicant Details', {
            'fields': ('applicant_name', 'franchise_name', 'email', 'mobile')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Agreement Details', {
            'fields': ('agreement_date', 'validity_date', 'notes')
        }),
        ('Courses & Payment', {
            'fields': ('selected_courses', 'total_amount', 'request_id')
        }),
        ('Status', {
            'fields': ('status', 'user_created')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# ============================================
# 1️⃣3️⃣ FRANCHISE ADMIN
# ============================================
@admin.register(Franchise)
class FranchiseAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'phone', 'email', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'city', 'state']
    search_fields = ['name', 'code', 'email', 'phone', 'address']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Contact Details', {
            'fields': ('phone', 'email')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# ============================================
# 1️⃣4️⃣ APPLICANT ADMIN
# ============================================
@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'franchise', 'email', 'mobile', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'city', 'state', 'franchise']
    search_fields = ['name', 'email', 'mobile', 'address']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    autocomplete_fields = ['franchise']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'mobile')
        }),
        ('Franchise', {
            'fields': ('franchise',)
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# ============================================
# 1️⃣5️⃣ FRANCHISE USER ADMIN (UPDATED)
# ============================================
@admin.register(FranchiseUser)
class FranchiseUserAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'franchise', 'franchise_code', 
        'applicant', 'is_active', 'is_verified', 'created_at'
    ]
    list_filter = ['is_active', 'is_verified', 'franchise']
    search_fields = [
        'user__username', 'user__email', 
        'franchise__name', 'franchise_code',
        'franchise_name', 'applicant__name', 'username'
    ]
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['user', 'franchise', 'applicant']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User Details', {
            'fields': ('user', 'username')
        }),
        ('Franchise Details', {
            'fields': ('franchise', 'franchise_code', 'franchise_name')
        }),
        ('Applicant', {
            'fields': ('applicant', 'applicant_name', 'email', 'mobile')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_permissions_count(self, obj):
        if obj.user:
            return obj.user.permissions.filter(granted=True).count()
        return 0
    get_permissions_count.short_description = 'Permissions Count'


# ============================================
# 1️⃣6️⃣ USER PERMISSION ADMIN
# ============================================
@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'permission_key', 'granted', 'granted_at', 'granted_by']
    list_filter = ['granted', 'permission_key', 'granted_at']
    search_fields = ['user__username', 'user__email', 'permission_key']
    readonly_fields = ['granted_at']
    autocomplete_fields = ['user', 'granted_by']
    ordering = ['-granted_at']
    
    fieldsets = (
        ('User & Permission', {
            'fields': ('user', 'permission_key', 'granted')
        }),
        ('Granted By', {
            'fields': ('granted_by',)
        }),
        ('Timestamps', {
            'fields': ('granted_at',)
        }),
    )
    
    actions = ['grant_permissions', 'revoke_permissions']
    
    def grant_permissions(self, request, queryset):
        updated = queryset.update(granted=True)
        self.message_user(request, f'✅ {updated} permission(s) granted.')
    grant_permissions.short_description = '✅ Grant selected permissions'
    
    def revoke_permissions(self, request, queryset):
        updated = queryset.update(granted=False)
        self.message_user(request, f'❌ {updated} permission(s) revoked.')
    revoke_permissions.short_description = '❌ Revoke selected permissions'


# ============================================
# 1️⃣7️⃣ FRANCHISE CERTIFICATE ADMIN
# ============================================
@admin.register(FranchiseCertificate)
class FranchiseCertificateAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'cert_no', 'applicant_name', 'franchise_name', 
        'course_name', 'franchise_code', 'status', 'created_at'
    ]
    list_filter = ['status', 'course_name']
    search_fields = ['cert_no', 'applicant_name', 'franchise_name', 'franchise_code']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Certificate Info', {
            'fields': ('cert_no', 'franchise_code', 'status')
        }),
        ('Applicant Info', {
            'fields': ('applicant_name', 'father_name', 'franchise_name', 'authorized_area')
        }),
        ('Course Info', {
            'fields': ('selected_category', 'course_name', 'validity_from', 'validity_to')
        }),
        ('Location', {
            'fields': ('city', 'state')
        }),
        ('Company Info', {
            'fields': (
                'center_coordinator', 'director', 'company_name', 
                'reg_no', 'website', 'iso', 'head_office', 
                'regional_office', 'phone', 'email'
            )
        }),
        ('Media', {
            'fields': ('applicant_photo', 'qr_image')
        }),
        ('Social Links', {
            'fields': ('social_links',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'created_by')
        }),
    )
    
    actions = ['activate_certificates', 'deactivate_certificates']
    
    def activate_certificates(self, request, queryset):
        updated = queryset.update(status='Active')
        self.message_user(request, f'✅ {updated} certificate(s) activated successfully.')
    activate_certificates.short_description = '✅ Activate selected certificates'
    
    def deactivate_certificates(self, request, queryset):
        updated = queryset.update(status='Inactive')
        self.message_user(request, f'❌ {updated} certificate(s) deactivated.')
    deactivate_certificates.short_description = '❌ Deactivate selected certificates'


# ============================================
# 1️⃣8️⃣ STUDENT CERTIFICATE ADMIN - UPDATED
# ============================================
@admin.register(StudentCertificate)
class StudentCertificateAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'cert_no',
        'enroll_no',
        'student_name',
        'father_name',
        'course_name',
        'grade',
        'duration',
        'student_type',
        'franchise_code',
        'is_downloaded',        # 🆕
        'download_count',       # 🆕
        'wallet_deducted',      # 🆕
        'created_at',
    ]
    list_filter = [
        'student_type',
        'grade',
        'relation',
        'is_downloaded',        # 🆕
        'wallet_deducted',      # 🆕
        'created_at',
    ]
    search_fields = [
        'cert_no',
        'enroll_no',
        'student_name',
        'father_name',
        'course_name',
        'franchise_code',
    ]
    readonly_fields = [
        'cert_no',              # 🆕 Auto-generate
        'enroll_no',            # 🆕 Auto-generate
        'is_downloaded',        # 🆕 Backend controlled
        'downloaded_at',        # 🆕 Backend controlled
        'download_count',       # 🆕 Backend controlled
        'wallet_deducted',      # 🆕 Backend controlled
        'created_at',
        'updated_at',
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('📜 Certificate Info', {
            'fields': ('cert_no', 'enroll_no')
        }),
        ('👤 Student Info', {
            'fields': (
                'student_name',
                'relation',
                'father_name',
                'course_name',
                'student_id',
                'student_type'
            )
        }),
        ('🎓 Certificate Details', {
            'fields': ('center_name', 'grade', 'duration', 'issue_date')
        }),
        ('🏢 Authority', {
            'fields': ('center_coordinator', 'director')
        }),
        ('🏛️ Company Info', {
            'fields': (
                'company_name',
                'reg_no',
                'website',
                'unit',
                'iso',
                'head_office',
                'regional_office',
                'phone',
                'email'
            )
        }),
        ('📸 Media', {
            'fields': ('student_photo', 'qr_image'),
            'classes': ('collapse',)  # 🆕 Collapsed by default
        }),
        ('🔥 Franchise Info', {
            'fields': ('franchise_code', 'franchise_name', 'created_by')
        }),
        # 🆕 NEW SECTION - Download Tracking
        ('💰 Wallet & Download Tracking', {
            'fields': (
                'is_downloaded',
                'downloaded_at',
                'download_count',
                'wallet_deducted',
            ),
            'classes': ('collapse',)
        }),
        ('🕐 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'mark_as_student',
        'mark_as_vocational',
        'reset_download_status',    # 🆕
        'mark_as_downloaded',       # 🆕
    ]

    def mark_as_student(self, request, queryset):
        updated = queryset.update(student_type='student')
        self.message_user(
            request,
            f'✅ {updated} certificate(s) marked as Student.'
        )
    mark_as_student.short_description = '✅ Mark as Student'

    def mark_as_vocational(self, request, queryset):
        updated = queryset.update(student_type='vocational')
        self.message_user(
            request,
            f'🔧 {updated} certificate(s) marked as Vocational.'
        )
    mark_as_vocational.short_description = '🔧 Mark as Vocational'

    # 🆕 NEW ACTION: Reset download status
    def reset_download_status(self, request, queryset):
        updated = queryset.update(
            is_downloaded=False,
            downloaded_at=None,
            download_count=0,
            wallet_deducted=False,
        )
        self.message_user(
            request,
            f'🔄 {updated} certificate(s) download status reset.'
        )
    reset_download_status.short_description = '🔄 Reset Download Status'

    # 🆕 NEW ACTION: Manually mark downloaded
    def mark_as_downloaded(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            is_downloaded=True,
            downloaded_at=timezone.now(),
        )
        self.message_user(
            request,
            f'✅ {updated} certificate(s) marked as downloaded.'
        )
    mark_as_downloaded.short_description = '📥 Mark as Downloaded'

    # ============================================
# 1️⃣9️⃣ COURSE CATEGORY ADMIN
# ============================================
@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'label', 'icon', 'created_at']
    search_fields = ['label']


# ============================================
# 2️⃣0️⃣ COURSE DURATION ADMIN
# ============================================
@admin.register(CourseDuration)
class CourseDurationAdmin(admin.ModelAdmin):
    list_display = ['id', 'value', 'created_at']
    search_fields = ['value']


# ============================================
# 2️⃣1️⃣ WEBSITE COURSE ADMIN
# ============================================
@admin.register(WebsiteCourse)
class WebsiteCourseAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'duration', 'fee', 'total_payment', 'is_professional', 'is_active', 'created_at']
    list_filter = ['category', 'is_professional', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


# ============================================
# 2️⃣2️⃣ WEBSITE ENQUIRY ADMIN
# ============================================
@admin.register(WebsiteEnquiry)
class WebsiteEnquiryAdmin(admin.ModelAdmin):
    list_display = ['id', 'student_name', 'course_name', 'mobile', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['student_name', 'mobile', 'course_name']
    readonly_fields = ['created_at']



    # ============================================
# 2️⃣3️⃣ CERTIFICATE WALLET ADMIN
# ============================================
@admin.register(CertificateWallet)
class CertificateWalletAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'franchise_code',
        'franchise_name',
        'total_certificates',
        'used_certificates',
        'remaining_certificates',
        'total_amount_paid',
        'is_active',
        'created_at',
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['franchise_code', 'franchise_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('🏷️ Franchise Info', {
            'fields': ('franchise_code', 'franchise_name')
        }),
        ('💰 Balance', {
            'fields': (
                'total_certificates',
                'used_certificates',
                'remaining_certificates',
                'total_amount_paid',
            )
        }),
        ('📌 Status', {
            'fields': ('is_active',)
        }),
        ('🕐 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================
# 2️⃣4️⃣ CERTIFICATE PACKAGE ADMIN
# ============================================
@admin.register(CertificatePackage)
class CertificatePackageAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'certificate_count',
        'price',
        'per_certificate_price',
        'discount_percentage',
        'status',
        'is_popular',
        'created_at',
    ]
    list_filter = ['status', 'is_popular']
    search_fields = ['name']
    list_editable = ['status', 'is_popular', 'price']
    readonly_fields = ['per_certificate_price', 'created_at', 'updated_at']
    ordering = ['certificate_count']

    fieldsets = (
        ('📦 Package Info', {
            'fields': ('name', 'description')
        }),
        ('💰 Pricing', {
            'fields': (
                'certificate_count',
                'price',
                'per_certificate_price',
                'discount_percentage',
                'original_price',
            )
        }),
        ('📌 Status', {
            'fields': ('status', 'is_popular')
        }),
        ('🕐 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================
# 2️⃣5️⃣ WALLET TRANSACTION ADMIN
# ============================================
@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'franchise_code',
        'transaction_type',
        'certificate_count',
        'amount',
        'balance_before',
        'balance_after',
        'payment_method',
        'payment_status',
        'created_at',
    ]
    list_filter = [
        'transaction_type',
        'payment_method',
        'payment_status',
        'created_at',
    ]
    search_fields = [
        'franchise_code',
        'razorpay_payment_id',
        'razorpay_order_id',
        'payment_reference',
        'remarks',
    ]
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('🔗 References', {
            'fields': ('wallet', 'package', 'certificate')
        }),
        ('🧾 Transaction Details', {
            'fields': (
                'transaction_type',
                'franchise_code',
                'certificate_count',
                'amount',
            )
        }),
        ('💰 Balance', {
            'fields': ('balance_before', 'balance_after')
        }),
        ('💳 Payment', {
            'fields': (
                'payment_method',
                'payment_status',
                'payment_reference',
            )
        }),
        ('🔒 Razorpay', {
            'fields': (
                'razorpay_order_id',
                'razorpay_payment_id',
                'razorpay_signature',
            ),
            'classes': ('collapse',)
        }),
        ('📝 Meta', {
            'fields': ('remarks', 'created_by', 'created_at')
        }),
    )