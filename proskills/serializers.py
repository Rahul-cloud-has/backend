# proskills/serializers.py - COMPLETE CLASS-BASED SERIALIZERS

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Category, Session, Course, Job, 
    FranchisePayment, Student, Payment,
    VocationalStudent, VocationalPayment,
    Application, GeneratedFranchise,
    Franchise, Applicant, FranchiseUser,
    UserPermission, FranchiseCertificate,
    StudentCertificate,
     CourseCategory,
    CourseDuration,
    WebsiteCourse,
    WebsiteEnquiry,
     StudentCertificate,
        CertificateWallet,
        CertificatePackage,
        WalletTransaction,
)


# ============================================
# 1️⃣ USER SERIALIZER
# ============================================
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


# ============================================
# 2️⃣ CATEGORY SERIALIZER
# ============================================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


# ============================================
# 3️⃣ SESSION SERIALIZER
# ============================================
class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'


# ============================================
# 4️⃣ COURSE SERIALIZER
# ============================================
class CourseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    session_name = serializers.CharField(source='sessions.name', read_only=True)
    
    class Meta:
        model = Course
        fields = '__all__'


# ============================================
# 5️⃣ LOGIN SERIALIZER
# ============================================
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        attrs['user'] = user
        return attrs


# ============================================
# 6️⃣ JOB SERIALIZER
# ============================================
class JobSerializer(serializers.ModelSerializer):
    posted_by_name = serializers.CharField(source='posted_by.username', read_only=True, required=False)
    
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# ============================================
# 7️⃣ FRANCHISE PAYMENT SERIALIZER
# ============================================
class FranchisePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FranchisePayment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

# ============================================
# 8️⃣ STUDENT SERIALIZER
# ============================================
class StudentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Student
        fields = '__all__'


# ============================================
# 9️⃣ PAYMENT SERIALIZER
# ============================================
class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = '__all__'
# ============================================
# 🔧 VOCATIONAL STUDENT SERIALIZER
# ============================================
class VocationalStudentSerializer(serializers.ModelSerializer):

    class Meta:
        model = VocationalStudent
        fields = '__all__'


# ============================================
# 💳 VOCATIONAL PAYMENT SERIALIZER
# ============================================
class VocationalPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = VocationalPayment
        fields = '__all__'
# ============================================
# 1️⃣2️⃣ APPLICATION SERIALIZER
# ============================================
class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'


# ============================================
# 1️⃣3️⃣ GENERATED FRANCHISE SERIALIZER
# ============================================
class GeneratedFranchiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedFranchise
        fields = '__all__'


# ============================================
# 1️⃣4️⃣ FRANCHISE SERIALIZER
# ============================================
class FranchiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Franchise
        fields = [
            'id', 'name', 'code', 'address', 'city', 'state',
            'pincode', 'phone', 'email', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


# ============================================
# 1️⃣5️⃣ APPLICANT SERIALIZER
# ============================================
class ApplicantSerializer(serializers.ModelSerializer):
    franchise_name = serializers.CharField(source='franchise.name', read_only=True)
    franchise_code = serializers.CharField(source='franchise.code', read_only=True)

    class Meta:
        model = Applicant
        fields = [
            'id', 'franchise', 'franchise_name', 'franchise_code',
            'name', 'username', 'email', 'mobile',
            'address', 'city', 'state', 'pincode',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


# ============================================
# 1️⃣6️⃣ USER PERMISSION SERIALIZER
# ============================================
class UserPermissionSerializer(serializers.ModelSerializer):
    permission_display = serializers.CharField(source='get_permission_key_display', read_only=True)

    class Meta:
        model = UserPermission
        fields = ['id', 'permission_key', 'permission_display', 'granted', 'granted_at']
        read_only_fields = ['granted_at']


# ============================================
# 1️⃣7️⃣ FRANCHISE USER SERIALIZER (Full) - WITH VALIDITY DATE
# ============================================
class FranchiseUserSerializer(serializers.ModelSerializer):
    
    user = UserSerializer(read_only=True)
    franchise = FranchiseSerializer(read_only=True)
    applicant = ApplicantSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = FranchiseUser
        fields = [
            'id', 'user', 'franchise', 'applicant', 'generated_franchise',
            'username', 'franchise_code', 'franchise_name',
            'applicant_name', 'email', 'mobile',
            'address', 'city', 'state', 'pincode',
            'validity_date',  # 🔥 ADDED - Expiry Date
            'permissions', 'password',
            'is_active', 'is_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_permissions(self, obj):
        if obj.user:
            return UserPermissionSerializer(obj.user.permissions.all(), many=True).data
        return []
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        
        username = validated_data.get('username')
        email = validated_data.get('email', '')
        
        if username and User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'Username already exists'})
        
        if not username:
            import random
            username = f"user_{random.randint(1000, 9999)}"
        
        if not password:
            import random
            import string
            password = ''.join(random.choices(string.ascii_letters + string.digits + '@#$', k=12))
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )
        
        if not validated_data.get('franchise_code'):
            import datetime
            year = datetime.datetime.now().year
            last = FranchiseUser.objects.filter(
                franchise_code__startswith=f'FR-{year}'
            ).count()
            validated_data['franchise_code'] = f'FR-{year}-{str(last + 1).zfill(4)}'
        
        franchise_user = FranchiseUser.objects.create(
            user=user,
            **validated_data
        )
        
        franchise_user._generated_password = password
        
        return franchise_user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        user = instance.user
        if 'username' in validated_data:
            user.username = validated_data.pop('username')
        if 'email' in validated_data:
            user.email = validated_data.pop('email')
        if password:
            user.set_password(password)
        user.save()
        
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        
        if password:
            instance._generated_password = password
        
        return instance
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, '_generated_password'):
            data['password'] = instance._generated_password
        return data


# ============================================
# 1️⃣8️⃣ FRANCHISE USER LIST SERIALIZER - WITH VALIDITY DATE
# ============================================
class FranchiseUserListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    franchise = FranchiseSerializer(read_only=True)
    applicant = ApplicantSerializer(read_only=True)
    permission_count = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()  # 🔥 BONUS: Check if expired

    class Meta:
        model = FranchiseUser
        fields = [
            'id', 'user', 'franchise', 'applicant',
            'username', 'franchise_code', 'franchise_name',
            'applicant_name', 'email', 'mobile',
            'address', 'city', 'state', 'pincode',
            'validity_date',  # 🔥 ADDED - Expiry Date
            'is_expired',     # 🔥 BONUS: Frontend ko batayega expired hai ya nahi
            'is_active', 'is_verified',
            'permission_count', 'permissions',
            'created_at', 'updated_at'
        ]

    def get_permission_count(self, obj):
        if obj.user:
            return obj.user.permissions.filter(granted=True).count()
        return 0

    def get_permissions(self, obj):
        if obj.user:
            return UserPermissionSerializer(obj.user.permissions.all(), many=True).data
        return []
    
    def get_is_expired(self, obj):
        """Check if franchise access has expired"""
        if obj.validity_date:
            import datetime
            return obj.validity_date < datetime.date.today()
        return False
# ============================================
# 1️⃣9️⃣ FRANCHISE USER CREATE SERIALIZER
# ============================================
class FranchiseUserCreateSerializer(serializers.Serializer):
    franchise_id = serializers.IntegerField(required=True)
    permissions = serializers.DictField(
        child=serializers.BooleanField(),
        required=False,
        default=dict
    )

    def validate_franchise_id(self, value):
        try:
            generated_franchise = GeneratedFranchise.objects.get(id=value)
            if generated_franchise.user_created:
                raise serializers.ValidationError("User already created for this franchise")
            return value
        except GeneratedFranchise.DoesNotExist:
            raise serializers.ValidationError("Franchise not found")

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        import random
        import string
        import datetime
        
        User = get_user_model()
        
        generated_franchise = GeneratedFranchise.objects.get(id=validated_data['franchise_id'])
        permissions = validated_data.get('permissions', {})
        
        # Generate username
        base_name = generated_franchise.applicant_name.lower().replace(' ', '')
        random_num = random.randint(100, 999)
        username = f"{base_name}{random_num}"
        
        while User.objects.filter(username=username).exists():
            random_num = random.randint(100, 999)
            username = f"{base_name}{random_num}"
        
        # Generate password
        chars = string.ascii_letters + string.digits + '@#$'
        password = ''.join(random.choices(chars, k=12))
        
        # Generate franchise_code
        year = datetime.datetime.now().year
        last = FranchiseUser.objects.filter(
            franchise_code__startswith=f'FR-{year}'
        ).count()
        franchise_code = f'FR-{year}-{str(last + 1).zfill(4)}'
        
        # Create User
        user = User.objects.create_user(
            username=username,
            password=password,
            email=generated_franchise.email,
            role='franchise',
            franchise_code=franchise_code,
            phone=generated_franchise.mobile
        )
        
        # Get or create Franchise
        franchise, created = Franchise.objects.get_or_create(
            code=franchise_code,
            defaults={
                'name': generated_franchise.franchise_name,
                'email': generated_franchise.email,
                'phone': generated_franchise.mobile,
                'address': generated_franchise.address,
                'city': generated_franchise.city,
                'state': generated_franchise.state,
                'pincode': generated_franchise.pincode
            }
        )
        
        # Create Applicant
        applicant = Applicant.objects.create(
            franchise=franchise,
            name=generated_franchise.applicant_name,
            email=generated_franchise.email,
            mobile=generated_franchise.mobile,
            address=generated_franchise.address,
            city=generated_franchise.city,
            state=generated_franchise.state,
            pincode=generated_franchise.pincode,
            username=username
        )
        
        # Create FranchiseUser
        franchise_user = FranchiseUser.objects.create(
            user=user,
            franchise=franchise,
            applicant=applicant,
            generated_franchise=generated_franchise,
            username=username,
            franchise_code=franchise_code,
            franchise_name=generated_franchise.franchise_name,
            applicant_name=generated_franchise.applicant_name,
            email=generated_franchise.email,
            mobile=generated_franchise.mobile,
            address=generated_franchise.address,
            city=generated_franchise.city,
            state=generated_franchise.state,
            pincode=generated_franchise.pincode,
            permissions=permissions,
            is_active=True,
            is_verified=True
        )
        
        # Save permissions
        for perm_key, granted in permissions.items():
            UserPermission.objects.create(
                user=user,
                permission_key=perm_key,
                granted=granted,
                granted_by=user
            )
        
        # Mark as user_created
        generated_franchise.user_created = True
        generated_franchise.save()
        
        # Save password for response
        franchise_user._generated_password = password
        
        return franchise_user


# ============================================
# 2️⃣0️⃣ PERMISSION UPDATE SERIALIZER
# ============================================
class PermissionUpdateSerializer(serializers.Serializer):
    permissions = serializers.DictField(
        child=serializers.BooleanField(),
        required=True
    )


# ============================================
# 2️⃣1️⃣ BULK PERMISSION UPDATE SERIALIZER
# ============================================
class BulkPermissionUpdateSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField())
    permission_key = serializers.CharField()
    granted = serializers.BooleanField()


# ============================================
# 2️⃣2️⃣ USER PROFILE SERIALIZER
# ============================================
class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    franchise = FranchiseSerializer(read_only=True)
    applicant = ApplicantSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = FranchiseUser
        fields = [
            'id', 'user', 'franchise', 'applicant',
            'username', 'franchise_code', 'franchise_name',
            'applicant_name', 'email', 'mobile',
            'address', 'city', 'state', 'pincode',
            'is_active', 'is_verified',
            'permissions', 'created_at', 'updated_at'
        ]
    
    def get_permissions(self, obj):
        if obj.user:
            return UserPermissionSerializer(obj.user.permissions.all(), many=True).data
        return []


# ============================================
# 2️⃣3️⃣ FRANCHISE WITH APPLICANTS SERIALIZER
# ============================================
class FranchiseWithApplicantsSerializer(FranchiseSerializer):
    applicants = ApplicantSerializer(many=True, read_only=True)
    total_applicants = serializers.IntegerField(source='applicants.count', read_only=True)

    class Meta(FranchiseSerializer.Meta):
        fields = FranchiseSerializer.Meta.fields + ['applicants', 'total_applicants']


# ============================================
# 2️⃣4️⃣ FRANCHISE USER STATS SERIALIZER
# ============================================
class FranchiseUserStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    total_permissions_granted = serializers.IntegerField()


# ============================================
# 2️⃣5️⃣ ALL PERMISSIONS SERIALIZER
# ============================================
class AllPermissionsSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    desc = serializers.CharField()
    category = serializers.CharField()
    default = serializers.BooleanField()


# ============================================
# 2️⃣6️⃣ FRANCHISE CERTIFICATE SERIALIZER
# ============================================
class FranchiseCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FranchiseCertificate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        if not data.get('applicant_name'):
            raise serializers.ValidationError({'applicant_name': 'Applicant name is required'})
        if not data.get('franchise_name'):
            raise serializers.ValidationError({'franchise_name': 'Franchise name is required'})
        if not data.get('course_name'):
            raise serializers.ValidationError({'course_name': 'Course name is required'})
        return data

# ============================================
# 📜 STUDENT CERTIFICATE SERIALIZER
# ============================================
class StudentCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentCertificate
        fields = '__all__'
        read_only_fields = [
            'id',
            'cert_no',
            'enroll_no',
            'is_downloaded',
            'downloaded_at',
            'download_count',
            'wallet_deducted',
            'created_at',
            'updated_at',
        ]

        # from .models import CourseCategory, CourseDuration, WebsiteCourse, WebsiteEnquiry

# ============================================
# 📂 COURSE CATEGORY SERIALIZER
# ============================================
class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = '__all__'


# ============================================
# ⏱️ COURSE DURATION SERIALIZER
# ============================================
class CourseDurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseDuration
        fields = '__all__'


# ============================================
# 📚 WEBSITE COURSE SERIALIZER
# ============================================
class WebsiteCourseSerializer(serializers.ModelSerializer):

    # ✅ image — blank/null allowed, URL validation skip
    image = serializers.URLField(
        max_length=500,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    class Meta:
        model = WebsiteCourse
        fields = '__all__'


# ============================================
# 📋 WEBSITE ENQUIRY SERIALIZER
# ============================================
class WebsiteEnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteEnquiry
        fields = '__all__'



        # ********************
        #      rozarpay Payment
        # ****************************

       


# ============================================
# 📜 STUDENT CERTIFICATE SERIALIZER
# ============================================
class StudentCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentCertificate
        fields = '__all__'
        read_only_fields = [
            'id',
            'cert_no',
            'enroll_no',
            'is_downloaded',
            'downloaded_at',
            'download_count',
            'wallet_deducted',
            'created_at',
            'updated_at',
        ]


# ============================================
# 💰 WALLET SERIALIZER
# ============================================
class CertificateWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateWallet
        fields = '__all__'


# ============================================
# 📦 PACKAGE SERIALIZER
# ============================================
class CertificatePackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificatePackage
        fields = '__all__'


# ============================================
# 🧾 TRANSACTION SERIALIZER
# ============================================
class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = '__all__'


# ... aapke baaki serializers yahan