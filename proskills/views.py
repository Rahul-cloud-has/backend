# api/views.py - Complete Class-Based Views

from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import Http404
from django.db.models import Q, Count
from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
import logging
import random
import string
import datetime as dt
from decimal import Decimal

logger = logging.getLogger(__name__)
from .models import *
from .serializers import *

# ============================================
# 🔐 LOGIN VIEW - WITH EXPIRY CHECK (using dt)
# ============================================
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        login_type = request.data.get("login_type")

        if login_type == "admin":
            if user.role != "admin":
                return Response(
                    {"error": "Access Denied! This account is not an Admin account."},
                    status=status.HTTP_403_FORBIDDEN
                )

        elif login_type == "franchise":
            if user.role != "franchise":
                return Response(
                    {"error": "Please login from Admin Login."},
                    status=status.HTTP_403_FORBIDDEN
                )

            try:
                franchise_user = FranchiseUser.objects.get(user=user)

                # 🔒 EXPIRY DATE CHECK (using dt.date.today())
                if franchise_user.validity_date and franchise_user.validity_date < dt.date.today():
                    return Response(
                        {
                            "error": "Your franchise access validity has expired. Please contact admin for renewal."
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )

            except FranchiseUser.DoesNotExist:
                return Response(
                    {"error": "Franchise user profile not found."},
                    status=status.HTTP_403_FORBIDDEN
                )

        refresh = RefreshToken.for_user(user)

        if login_type == "franchise" and hasattr(user, 'franchise_code'):
            refresh['franchise_code'] = user.franchise_code

        # ✅ Base response
        response_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }

        # ✅ Franchise user ke liye permissions + validity_date add karo
        if login_type == "franchise":
            try:
                fu = FranchiseUser.objects.get(user=user)

                # ✅ Permissions
                permissions = fu.permissions or {}

                # ✅ franchise_user object response me add karo
                response_data["franchise_user"] = {
                    "id": fu.id,
                    "username": user.username,
                    "franchise_code": fu.franchise_code or getattr(user, 'franchise_code', ''),
                    "franchise_name": fu.franchise_name or getattr(user, 'franchise_name', ''),
                    "applicant_name": fu.applicant_name or '',
                    "email": fu.email or user.email or '',
                    "mobile": fu.mobile or getattr(user, 'mobile', '') or '',
                    "is_active": fu.is_active,
                    "validity_date": fu.validity_date.isoformat() if fu.validity_date else None,
                    "permissions": permissions,
                }

                print(f"✅ Franchise Login: {user.username}")
                print(f"✅ Permissions: {permissions}")
                print(f"📅 Validity Date: {fu.validity_date}")

            except FranchiseUser.DoesNotExist:
                response_data["franchise_user"] = None
            except Exception as e:
                print(f"❌ Error: {e}")
                response_data["franchise_user"] = None

        return Response(response_data)
# ============================================
# 📤 FRANCHISE USER LIST/CREATE
# ============================================
class FranchiseUserListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = FranchiseUser.objects.all().select_related(
            'user', 'franchise', 'applicant', 'generated_franchise'
        )
        
        search = request.query_params.get('search', '')
        franchise_id = request.query_params.get('franchise', '')
        
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(franchise__name__icontains=search) |
                Q(franchise__code__icontains=search) |
                Q(applicant__name__icontains=search) |
                Q(franchise_code__icontains=search) |
                Q(franchise_name__icontains=search) |
                Q(applicant_name__icontains=search) |
                Q(username__icontains=search)
            )
        if franchise_id:
            queryset = queryset.filter(franchise_id=franchise_id)
        
        serializer = FranchiseUserListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        print("=" * 60)
        print("📥 FRANCHISE USER CREATE - DATA RECEIVED:")
        print(request.data)
        print("=" * 60)
        
        data = request.data.copy()
        franchise_id = data.get('franchise_id')
        permissions = data.get('permissions', {})
        
        if not franchise_id:
            return Response({
                'status': 'error',
                'message': 'franchise_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            generated_franchise = GeneratedFranchise.objects.get(id=franchise_id)
        except GeneratedFranchise.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'Generated franchise with id {franchise_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if generated_franchise.user_created:
            return Response({
                'status': 'error',
                'message': 'User already created for this franchise'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 🔥 VALIDITY / EXPIRY DATE
        validity_date = (
            data.get('validity_date')
            or data.get('expiry_date')
            or getattr(generated_franchise, 'validity_date', None)
        )
        
        try:
            with transaction.atomic():
                # Generate Username
                base_name = generated_franchise.applicant_name.lower().replace(' ', '')
                random_num = random.randint(100, 999)
                username = f"{base_name}{random_num}"
                
                while User.objects.filter(username=username).exists():
                    random_num = random.randint(100, 999)
                    username = f"{base_name}{random_num}"
                
                # Generate Password
                chars = string.ascii_letters + string.digits + '@#$'
                password = ''.join(random.choices(chars, k=12))
                
                # Generate Franchise Code
                year = dt.datetime.now().year
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
                    validity_date=validity_date,  # 🔥 SAVE EXPIRY DATE
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
                        granted_by=request.user
                    )
                
                # Mark as user_created
                generated_franchise.user_created = True
                generated_franchise.save()
                
                print("✅ USER CREATED SUCCESSFULLY!")
                print(f"👤 Username: {username}")
                print(f"🔑 Password: {password}")
                print(f"🏷️ Franchise Code: {franchise_code}")
                print(f"📅 Validity Date: {validity_date}")
                print("=" * 60)
                
                return Response({
                    'status': 'success',
                    'message': 'Franchise user created successfully',
                    'data': {
                        'id': franchise_user.id,
                        'username': username,
                        'password': password,
                        'franchise_code': franchise_code,
                        'franchise_name': generated_franchise.franchise_name,
                        'applicant_name': generated_franchise.applicant_name,
                        'validity_date': validity_date,  # 🔥 RESPONSE ME BHI
                        'permissions': permissions
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error creating franchise user: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# 📤 FRANCHISE USER DETAIL
# ============================================
class FranchiseUserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return FranchiseUser.objects.select_related(
                'user', 'franchise', 'applicant', 'generated_franchise'
            ).get(pk=pk)
        except FranchiseUser.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        franchise_user = self.get_object(pk)
        serializer = FranchiseUserSerializer(franchise_user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, pk):
        franchise_user = self.get_object(pk)
        data = request.data.copy()
        
        try:
            with transaction.atomic():
                user = franchise_user.user
                
                # Update username if provided
                if 'username' in data and data['username']:
                    new_username = data['username'].strip()
                    if new_username != user.username:
                        if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                            return Response({
                                'status': 'error',
                                'message': f'Username "{new_username}" already exists'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        user.username = new_username
                        franchise_user.username = new_username
                
                # Update password if provided and not empty
                if 'password' in data and data['password'] and data['password'].strip():
                    user.set_password(data['password'].strip())
                
                # Update is_active
                if 'is_active' in data:
                    franchise_user.is_active = data['is_active']
                    user.is_active = data['is_active']
                
                # 🔥 UPDATE VALIDITY / EXPIRY DATE (For Renewal)
                if 'validity_date' in data or 'expiry_date' in data:
                    new_validity = data.get('validity_date') or data.get('expiry_date')
                    franchise_user.validity_date = new_validity
                
                # Update permissions if provided
                if 'permissions' in data:
                    permissions = data['permissions']
                    UserPermission.objects.filter(user=user).delete()
                    for perm_key, granted in permissions.items():
                        UserPermission.objects.create(
                            user=user,
                            permission_key=perm_key,
                            granted=granted,
                            granted_by=request.user
                        )
                    franchise_user.permissions = permissions
                
                user.save()
                franchise_user.save()
                
                response_data = {
                    'id': franchise_user.id,
                    'username': user.username,
                    'is_active': franchise_user.is_active,
                    'franchise_code': franchise_user.franchise_code,
                    'franchise_name': franchise_user.franchise_name,
                    'applicant_name': franchise_user.applicant_name,
                    'validity_date': franchise_user.validity_date,  # 🔥 RESPONSE ME BHI
                    'permissions': franchise_user.permissions
                }
                
                if 'password' in data and data['password'] and data['password'].strip():
                    response_data['password'] = data['password'].strip()
                
                return Response({
                    'status': 'success',
                    'message': 'User updated successfully',
                    'data': response_data
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error updating user: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        franchise_user = self.get_object(pk)
        
        try:
            with transaction.atomic():
                user = franchise_user.user
                
                if franchise_user.generated_franchise:
                    franchise_user.generated_franchise.user_created = False
                    franchise_user.generated_franchise.save()
                
                UserPermission.objects.filter(user=user).delete()
                franchise_user.delete()
                user.delete()
                
                return Response({
                    'status': 'success',
                    'message': 'User deleted successfully'
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            logger.error(f"Error deleting user: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
# ============================================
# 🔐 PERMISSION UPDATE VIEW
# ============================================
class UserPermissionUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        permissions = request.data.get('permissions', {})
        
        try:
            with transaction.atomic():
                UserPermission.objects.filter(user=user).delete()
                
                for key, granted in permissions.items():
                    UserPermission.objects.create(
                        user=user,
                        permission_key=key,
                        granted=granted,
                        granted_by=request.user
                    )
                
                try:
                    franchise_user = FranchiseUser.objects.get(user=user)
                    franchise_user.permissions = permissions
                    franchise_user.save()
                except FranchiseUser.DoesNotExist:
                    pass
                
                return Response({
                    'status': 'success',
                    'message': 'Permissions updated successfully'
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error updating permissions: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# 📤 GENERATED FRANCHISE VIEWS
# ============================================
class GeneratedFranchiseListCreateView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        queryset = GeneratedFranchise.objects.all()
        search = request.query_params.get('search', '')
        
        if search:
            queryset = queryset.filter(
                Q(applicant_name__icontains=search) |
                Q(franchise_name__icontains=search) |
                Q(mobile__icontains=search) |
                Q(email__icontains=search)
            )
        
        serializer = GeneratedFranchiseSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = GeneratedFranchiseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GeneratedFranchiseDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get_object(self, pk):
        try:
            return GeneratedFranchise.objects.get(pk=pk)
        except GeneratedFranchise.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = GeneratedFranchiseSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        obj = self.get_object(pk)
        serializer = GeneratedFranchiseSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.delete()
        return Response({'message': 'Deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


# ============================================
# 📤 FRANCHISE VIEWS
# ============================================
class FranchiseListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = Franchise.objects.all()
        search = request.query_params.get('search', '')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        serializer = FranchiseSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = FranchiseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FranchiseDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return Franchise.objects.get(pk=pk)
        except Franchise.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = FranchiseSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        obj = self.get_object(pk)
        serializer = FranchiseSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.is_active = False
        obj.save()
        return Response({'message': 'Franchise deactivated'}, status=status.HTTP_200_OK)


# ============================================
# 📤 APPLICANT VIEWS
# ============================================
class ApplicantListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = Applicant.objects.all()
        franchise_id = request.query_params.get('franchise', '')
        search = request.query_params.get('search', '')
        
        if franchise_id:
            queryset = queryset.filter(franchise_id=franchise_id)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(mobile__icontains=search)
            )
        
        serializer = ApplicantSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ApplicantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApplicantDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return Applicant.objects.get(pk=pk)
        except Applicant.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = ApplicantSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        obj = self.get_object(pk)
        serializer = ApplicantSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.is_active = False
        obj.save()
        return Response({'message': 'Applicant deactivated'}, status=status.HTTP_200_OK)

# ============================================
# 📝 APPLICATION VIEWS
# ============================================

class ApplicationListCreateView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        queryset = Application.objects.all()
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search')
        
        if status_filter and status_filter != 'All':
            queryset = queryset.filter(status=status_filter)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(mobile__icontains=search) |
                Q(email__icontains=search) |
                Q(franchise_name__icontains=search)
            )
        
        serializer = ApplicationSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ApplicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApplicationDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get_object(self, pk):
        try:
            return Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = ApplicationSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        obj = self.get_object(pk)
        serializer = ApplicationSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.delete()
        return Response({'message': 'Deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


# ============================================
# 📧 APPLICATION STATUS UPDATE + SEND EMAIL
# ============================================
from django.core.mail import send_mail
from django.conf import settings


class ApplicationStatusUpdateView(APIView):
    """
    PATCH: Update application status (Approve/Reject) and send email to applicant
    URL: /api/applications/<int:pk>/status/
    """
    permission_classes = [AllowAny]
    
    def patch(self, request, pk):
        # ✅ Application find karo
        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # ✅ Data receive karo
        status_value = request.data.get('status')
        admin_note = request.data.get('admin_note', '')
        
        # ✅ Validate status
        if status_value not in ['Pending', 'Approved', 'Rejected']:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ✅ Status update
        old_status = application.status
        application.status = status_value
        if admin_note:
            application.admin_note = admin_note
        application.save()
        
        # ============================================
        # ✅ SEND EMAIL TO APPLICANT
        # ============================================
        email_status = 'Email not sent'
        applicant_email = application.email
        applicant_name = application.name or 'Applicant'
        
        if applicant_email:
            try:
                # ===== APPROVED EMAIL =====
                if status_value == 'Approved':
                    subject = '🎉 Congratulations! Your EduSkillVision Franchise Application is Approved'
                    message = f"""Dear {applicant_name},

Congratulations! We are pleased to inform you that your EduSkillVision Franchise Application has been APPROVED. ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 APPLICATION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Application ID    : #{application.id}
Applicant Name    : {applicant_name}
Father Name       : {application.father_name or 'N/A'}
Franchise Name    : {application.franchise_name or 'N/A'}
Mobile            : {application.mobile}
Email             : {application.email}
City / State      : {application.city}, {application.state}
Pincode           : {application.pincode}
Status            : APPROVED ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Admin Message:
{admin_note if admin_note else 'Welcome to the EduSkillVision family! Our team will contact you shortly for further processing.'}

🎯 NEXT STEPS:
Our team will contact you within 2-3 business days regarding:
   • Franchise Agreement
   • Training Schedule  
   • Setup Process
   • Documentation

For any queries, feel free to reach us:
📞 Phone : +91 8818800802
📧 Email : info@eduskillvision.com
🌐 Web   : www.eduskillvision.com

Thank you for choosing EduSkillVision!

Best Regards,
Team EduSkillVision
EMPOWERING SKILLS, SHAPING FUTURES
"""
                
                # ===== REJECTED EMAIL =====
                elif status_value == 'Rejected':
                    subject = 'Update on Your EduSkillVision Franchise Application'
                    message = f"""Dear {applicant_name},

Thank you for your interest in the EduSkillVision Franchise Program.

After careful review of your application, we regret to inform you that your application has not been approved at this time. ❌

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 APPLICATION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Application ID    : #{application.id}
Applicant Name    : {applicant_name}
Franchise Name    : {application.franchise_name or 'N/A'}
Mobile            : {application.mobile}
City / State      : {application.city}, {application.state}
Status            : REJECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Reason / Admin Note:
{admin_note if admin_note else 'Unfortunately your application did not meet our current requirements.'}

You are most welcome to reapply in the future once the requirements are fulfilled.

For any queries or clarification, please contact us:
📞 Phone : +91 8818800802
📧 Email : info@eduskillvision.com
🌐 Web   : www.eduskillvision.com

We appreciate your interest in EduSkillVision.

Best Regards,
Team EduSkillVision
EMPOWERING SKILLS, SHAPING FUTURES
"""
                
                # ===== PENDING EMAIL =====
                else:
                    subject = 'Your EduSkillVision Franchise Application is Under Review'
                    message = f"""Dear {applicant_name},

Your franchise application is currently under review.

Application ID: #{application.id}

We will notify you once the decision is made.

Best Regards,
Team EduSkillVision
"""
                
                # ✅ SEND EMAIL
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[applicant_email],
                    fail_silently=False,
                )
                
                email_status = f'Email sent successfully to {applicant_email}'
                print(f'✅ EMAIL SENT to {applicant_email} - Status: {status_value}')
                logger.info(f'Email sent to {applicant_email} - Status: {status_value}')
                
            except Exception as email_error:
                email_status = f'Email failed: {str(email_error)}'
                print(f'❌ EMAIL ERROR: {email_error}')
                logger.error(f'Email error: {email_error}')
        else:
            email_status = 'Applicant email not found'
            print('⚠️ No applicant email available')
        
        # ✅ Return response
        serializer = ApplicationSerializer(application)
        return Response({
            'success': True,
            'message': f'Application {status_value} successfully',
            'status': application.status,
            'email_status': email_status,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    # ✅ PUT method bhi support karo (backward compatibility)
    def put(self, request, pk):
        return self.patch(request, pk)

    
# ============================================
# 📜 FRANCHISE CERTIFICATE VIEWS
# ============================================
class FranchiseCertificateListCreateView(APIView):
    
    def get(self, request):
        queryset = FranchiseCertificate.objects.all()
        
        franchise_code = request.query_params.get('franchise_code')
        if franchise_code:
            queryset = queryset.filter(franchise_code=franchise_code)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(applicant_name__icontains=search) |
                Q(franchise_name__icontains=search) |
                Q(cert_no__icontains=search) |
                Q(course_name__icontains=search)
            )
        
        serializer = FranchiseCertificateSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.username if request.user.is_authenticated else 'admin'
        
        serializer = FranchiseCertificateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FranchiseCertificateDetailView(APIView):
    
    def get_object(self, pk):
        return get_object_or_404(FranchiseCertificate, pk=pk)
    
    def get(self, request, pk):
        certificate = self.get_object(pk)
        serializer = FranchiseCertificateSerializer(certificate)
        return Response(serializer.data)
    
    def put(self, request, pk):
        certificate = self.get_object(pk)
        serializer = FranchiseCertificateSerializer(certificate, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        certificate = self.get_object(pk)
        serializer = FranchiseCertificateSerializer(certificate, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        certificate = self.get_object(pk)
        certificate.delete()
        return Response({'message': 'Deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class FranchiseCertificateStatsView(APIView):
    
    def get(self, request):
        franchise_code = request.query_params.get('franchise_code')
        queryset = FranchiseCertificate.objects.all()
        
        if franchise_code:
            queryset = queryset.filter(franchise_code=franchise_code)
        
        return Response({
            'total': queryset.count(),
            'active': queryset.filter(status='Active').count(),
            'expired': queryset.filter(status='Expired').count(),
            'inactive': queryset.filter(status='Inactive').count(),
            'generated': queryset.filter(status='Generated').count(),
        })


class FranchiseCertificateByFranchiseView(APIView):
    
    def get(self, request):
        franchise_code = request.query_params.get('franchise_code')
        
        if not franchise_code:
            return Response(
                {'error': 'franchise_code parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        certificates = FranchiseCertificate.objects.filter(franchise_code=franchise_code)
        serializer = FranchiseCertificateSerializer(certificates, many=True)
        return Response(serializer.data)

# ✅ ADD ye naye views:
# # ============================================
# # 📜 CERTIFICATE LIST + CREATE VIEW
# # ============================================
# class StudentCertificateListCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         """
#         GET: List all certificates
#         - Franchise: Only own certificates
#         - Admin: All certificates
#         """
#         user = request.user
#         queryset = StudentCertificate.objects.all()

#         # 🔥 Franchise-wise filter
#         if getattr(user, 'role', '') == 'franchise':
#             queryset = queryset.filter(franchise_code=user.franchise_code)
#         else:
#             # Admin sees all (removed old restriction)
#             pass

#         # Extra filters
#         student_type = request.query_params.get('student_type')
#         if student_type:
#             queryset = queryset.filter(student_type=student_type)

#         search = request.query_params.get('search')
#         if search:
#             queryset = queryset.filter(
#                 Q(student_name__icontains=search) |
#                 Q(course_name__icontains=search) |
#                 Q(cert_no__icontains=search) |
#                 Q(father_name__icontains=search) |
#                 Q(enroll_no__icontains=search)
#             )

#         serializer = StudentCertificateSerializer(queryset, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         """
#         POST: Create new certificate
#         - Franchise: Save + return wallet balance
#         - Admin: Save with 'Admin' tag
#         """
#         data = request.data.copy()
#         user = request.user

#         # 🔥 Auto-assign franchise
#         if getattr(user, 'role', '') == 'franchise':
#             data['franchise_code'] = user.franchise_code
#             data['franchise_name'] = getattr(user, 'franchise_name', '')
#             data['created_by'] = user.username
#         else:
#             data['franchise_code'] = ''
#             data['franchise_name'] = 'Admin'
#             data['created_by'] = 'admin'

#         serializer = StudentCertificateSerializer(data=data)
#         if serializer.is_valid():
#             cert = serializer.save()

#             # 💰 Return wallet balance for franchise (frontend expects this)
#             wallet_remaining = None
#             if getattr(user, 'role', '') == 'franchise':
#                 # TODO: Get from CertificateWallet model (when created)
#                 # For now, return None
#                 wallet_remaining = None

#             return Response({
#                 "message": "Certificate Generated Successfully",
#                 "data": StudentCertificateSerializer(cert).data,
#                 "wallet_remaining": wallet_remaining,
#             }, status=status.HTTP_201_CREATED)

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )


# # ============================================
# # 📜 CERTIFICATE DETAIL VIEW (Get/Update/Delete)
# # ============================================
# class StudentCertificateDetailView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get_object(self, pk):
#         try:
#             return StudentCertificate.objects.get(id=pk)
#         except StudentCertificate.DoesNotExist:
#             return None

#     def get(self, request, pk):
#         """GET: Single certificate by ID"""
#         cert = self.get_object(pk)
#         if not cert:
#             return Response(
#                 {"error": "Certificate not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         # Franchise can only view own certificates
#         user = request.user
#         if getattr(user, 'role', '') == 'franchise':
#             if cert.franchise_code != user.franchise_code:
#                 return Response(
#                     {"error": "Access denied"},
#                     status=status.HTTP_403_FORBIDDEN
#                 )

#         serializer = StudentCertificateSerializer(cert)
#         return Response(serializer.data)

#     def put(self, request, pk):
#         """PUT: Full update"""
#         cert = self.get_object(pk)
#         if not cert:
#             return Response(
#                 {"error": "Certificate not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         # Franchise permission check
#         user = request.user
#         if getattr(user, 'role', '') == 'franchise':
#             if cert.franchise_code != user.franchise_code:
#                 return Response(
#                     {"error": "Access denied"},
#                     status=status.HTTP_403_FORBIDDEN
#                 )

#         serializer = StudentCertificateSerializer(
#             cert, data=request.data, partial=True
#         )
#         if serializer.is_valid():
#             serializer.save()
#             return Response({
#                 "message": "Certificate Updated Successfully",
#                 "data": serializer.data,
#             })

#         return Response(
#             serializer.errors,
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     def patch(self, request, pk):
#         """PATCH: Partial update"""
#         return self.put(request, pk)

#     def delete(self, request, pk):
#         """DELETE: Remove certificate"""
#         cert = self.get_object(pk)
#         if not cert:
#             return Response(
#                 {"error": "Certificate not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         # Franchise permission check
#         user = request.user
#         if getattr(user, 'role', '') == 'franchise':
#             if cert.franchise_code != user.franchise_code:
#                 return Response(
#                     {"error": "Access denied"},
#                     status=status.HTTP_403_FORBIDDEN
#                 )

#         cert_no = cert.cert_no
#         cert.delete()

#         return Response({
#             "message": f"Certificate {cert_no} Deleted Successfully"
#         }, status=status.HTTP_204_NO_CONTENT)


# # ============================================
# # 📊 CERTIFICATE STATS VIEW
# # ============================================
# class StudentCertificateStatsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         """GET: Statistics"""
#         user = request.user
#         queryset = StudentCertificate.objects.all()

#         # Franchise filter
#         if getattr(user, 'role', '') == 'franchise':
#             queryset = queryset.filter(franchise_code=user.franchise_code)

#         return Response({
#             'total': queryset.count(),
#             'student': queryset.filter(student_type='student').count(),
#             'vocational': queryset.filter(student_type='vocational').count(),
#             'downloaded': queryset.filter(is_downloaded=True).count(),
#             'not_downloaded': queryset.filter(is_downloaded=False).count(),
#         })

# # ============================================
# # 📥 MARK CERTIFICATE AS DOWNLOADED + WALLET DEDUCT
# # ============================================
# class MarkCertificateDownloadedView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, pk):
#         # 🔥 DEBUG PRINTS
#         print("\n" + "="*60)
#         print("🔥 DOWNLOAD API HIT!")
#         print(f"   Cert ID: {pk}")
#         print(f"   User: {request.user}")
#         print(f"   Role: {getattr(request.user, 'role', 'NO ROLE')}")
#         print("="*60)
        
#         from .models import CertificateWallet, WalletTransaction

#         try:
#             cert = StudentCertificate.objects.get(id=pk)
#         except StudentCertificate.DoesNotExist:
#             return Response({"error": "Certificate not found"}, status=404)

#         print(f"✅ Certificate Found: {cert.cert_no}")
#         print(f"   Franchise Code: {cert.franchise_code}")
#         print(f"   wallet_deducted: {cert.wallet_deducted}")

#         user = request.user

#         # Permission check
#         if getattr(user, 'role', '') == 'franchise':
#             if cert.franchise_code != user.franchise_code:
#                 return Response({"error": "Access denied"}, status=403)

#         is_first_download = not cert.wallet_deducted
#         print(f"   is_first_download: {is_first_download}")
        
#         wallet_deducted_now = False
#         wallet_remaining = None

#         if is_first_download:
#             wallet = CertificateWallet.objects.filter(
#                 franchise_code=cert.franchise_code
#             ).first()
            
#             print(f"💰 Wallet: {wallet}")
#             if wallet:
#                 print(f"   Remaining BEFORE: {wallet.remaining_certificates}")

#             if not wallet:
#                 print("❌ WALLET NOT FOUND!")
#                 return Response({
#                     "error": "Wallet not found",
#                     "message": "Please purchase a package first."
#                 }, status=404)

#             if wallet.remaining_certificates <= 0:
#                 print("❌ WALLET EMPTY!")
#                 return Response({
#                     "error": "Insufficient balance",
#                     "remaining": 0
#                 }, status=400)

#             # ✅ DEDUCT
#             balance_before = wallet.remaining_certificates
#             wallet.remaining_certificates -= 1
#             wallet.used_certificates = (wallet.used_certificates or 0) + 1
#             wallet.save()
            
#             print(f"✅ WALLET DEDUCTED!")
#             print(f"   Remaining AFTER: {wallet.remaining_certificates}")

#             # Create transaction
#             WalletTransaction.objects.create(
#                 wallet=wallet,
#                 certificate=cert,
#                 transaction_type='deduction',
#                 franchise_code=cert.franchise_code,
#                 certificate_count=1,
#                 amount=0,
#                 balance_before=balance_before,
#                 balance_after=wallet.remaining_certificates,
#                 remarks=f'Certificate downloaded: {cert.student_name} ({cert.cert_no})',
#                 created_by=getattr(user, 'username', 'system'),
#             )

#             cert.wallet_deducted = True
#             wallet_deducted_now = True
#             wallet_remaining = wallet.remaining_certificates
#         else:
#             print("⏭️ ALREADY DEDUCTED")
#             wallet = CertificateWallet.objects.filter(
#                 franchise_code=cert.franchise_code
#             ).first()
#             if wallet:
#                 wallet_remaining = wallet.remaining_certificates

#         cert.mark_downloaded()
        
#         print("="*60 + "\n")

#         return Response({
#             "success": True,
#             "message": "Certificate downloaded successfully",
#             "cert_no": cert.cert_no,
#             "download_count": cert.download_count,
#             "wallet_deducted": wallet_deducted_now,
#             "wallet_remaining": wallet_remaining,
#             "is_first_download": is_first_download,
#         }, status=200)
    
# ============================================
# 📊 USER PERMISSIONS VIEW
# ============================================
class UserPermissionsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        permissions = UserPermission.objects.filter(user=user)
        serializer = UserPermissionSerializer(permissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================
# 📊 ALL PERMISSIONS VIEW
# ============================================
class AllPermissionsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .permissions_config import ALL_PERMISSIONS
        return Response(ALL_PERMISSIONS, status=status.HTTP_200_OK)


# ============================================
# 📊 FRANCHISE USER STATS VIEW
# ============================================
class FranchiseUserStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        stats = {
            'total_users': FranchiseUser.objects.count(),
            'active_users': FranchiseUser.objects.filter(is_active=True).count(),
            'verified_users': FranchiseUser.objects.filter(is_verified=True).count(),
            'total_permissions_granted': UserPermission.objects.filter(granted=True).count(),
        }
        
        franchise_stats = Franchise.objects.annotate(
            user_count=Count('users')
        ).values('id', 'name', 'code', 'user_count')
        
        stats['franchise_stats'] = list(franchise_stats)
        
        return Response(stats, status=status.HTTP_200_OK)


# ============================================
# 👤 USER PROFILE VIEW
# ============================================
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            franchise_user = FranchiseUser.objects.get(user=request.user)
            serializer = UserProfileSerializer(franchise_user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except FranchiseUser.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============================================
# 🔄 BULK PERMISSION UPDATE VIEW
# ============================================
class BulkPermissionUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = BulkPermissionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        user_ids = data['user_ids']
        permission_key = data['permission_key']
        granted = data['granted']
        
        try:
            users = User.objects.filter(id__in=user_ids)
            
            with transaction.atomic():
                for user in users:
                    UserPermission.objects.update_or_create(
                        user=user,
                        permission_key=permission_key,
                        defaults={
                            'granted': granted,
                            'granted_by': request.user
                        }
                    )
            
            return Response({
                'message': f'Permissions updated for {users.count()} users',
                'updated_count': users.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in bulk permission update: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================
# 📚 CATEGORY VIEWS
# ============================================
class CategoryListCreateView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = CategorySerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        obj = self.get_object(pk)
        serializer = CategorySerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.delete()
        return Response({'message': 'Deleted'}, status=status.HTTP_204_NO_CONTENT)


# ============================================
# 📚 SESSION VIEWS
# ============================================
class SessionListCreateView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        sessions = Session.objects.all()
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = SessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SessionDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get_object(self, pk):
        try:
            return Session.objects.get(pk=pk)
        except Session.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = SessionSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        obj = self.get_object(pk)
        serializer = SessionSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.delete()
        return Response({'message': 'Deleted'}, status=status.HTTP_204_NO_CONTENT)


# ============================================
# 📚 COURSE VIEWS
# ============================================
class CourseListCreateView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        courses = Course.objects.filter(is_active=True)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get_object(self, pk):
        try:
            return Course.objects.get(pk=pk, is_active=True)
        except Course.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = CourseSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        try:
            obj = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CourseSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            obj = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        
        obj.is_active = False
        obj.save()
        return Response({'message': 'Course deactivated'}, status=status.HTTP_200_OK)


# ============================================
# 💼 JOB VIEWS
# ============================================
class JobListCreateView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        jobs = Job.objects.filter(is_active=True).order_by('-created_at')
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user if request.user.is_authenticated else None
            serializer.save(posted_by=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get_object(self, pk):
        try:
            return Job.objects.get(pk=pk, is_active=True)
        except Job.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = JobSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        try:
            obj = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = JobSerializer(obj, data=request.data)
        if serializer.is_valid():
            user = request.user if request.user.is_authenticated else None
            serializer.save(posted_by=user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            obj = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
        
        obj.is_active = False
        obj.save()
        return Response({'message': 'Job deactivated'}, status=status.HTTP_200_OK)


# ============================================
# 💳 FRANCHISE PAYMENT VIEWS
# ============================================
class FranchisePaymentListCreateView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        payments = FranchisePayment.objects.all().order_by('-created_at')
        serializer = FranchisePaymentSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = FranchisePaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FranchisePaymentDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get_object(self, pk):
        try:
            return FranchisePayment.objects.get(pk=pk)
        except FranchisePayment.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        obj = self.get_object(pk)
        serializer = FranchisePaymentSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        obj = self.get_object(pk)
        serializer = FranchisePaymentSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        obj = self.get_object(pk)
        obj.delete()
        return Response({'message': 'Deleted'}, status=status.HTTP_204_NO_CONTENT)

    # ============================================
# 👨‍🎓 STUDENT VIEWS - FRANCHISE SAFE
# ============================================

class StudentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_franchise_context(self, user):
        """Helper: User ka role check karo"""
        is_franchise = hasattr(user, 'role') and user.role == 'franchise'
        return {
            'is_franchise': is_franchise,
            'franchise_code': getattr(user, 'franchise_code', '') if is_franchise else None,
            'franchise_name': getattr(user, 'franchise_name', '') if is_franchise else 'Admin',
        }

    # ✅ GET - List
    def get(self, request):
        user = request.user
        ctx = self.get_franchise_context(user)

        queryset = Student.objects.filter(status='Active')

        if ctx['is_franchise']:
            # 🔒 Franchise → sirf apna data
            queryset = queryset.filter(franchise_code=ctx['franchise_code'])
        else:
            # ✅ Admin → sirf apna (empty franchise_code)
            queryset = queryset.filter(
                Q(franchise_code__isnull=True) | Q(franchise_code='')
            )

        serializer = StudentSerializer(queryset.order_by('-created_at'), many=True)
        return Response(serializer.data)

    # ✅ POST - Create
    def post(self, request):
        data = request.data.copy()
        user = request.user
        ctx = self.get_franchise_context(user)

        if ctx['is_franchise']:
            # 🔒 Force apna franchise code
            data['franchise_code'] = ctx['franchise_code']
            data['franchise_name'] = ctx['franchise_name']
            data['created_by'] = user.username
        else:
            data['franchise_code'] = ''
            data['franchise_name'] = 'Admin'
            data['created_by'] = 'admin'

        serializer = StudentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Student added successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_franchise_context(self, user):
        is_franchise = hasattr(user, 'role') and user.role == 'franchise'
        return {
            'is_franchise': is_franchise,
            'franchise_code': getattr(user, 'franchise_code', '') if is_franchise else None,
            'franchise_name': getattr(user, 'franchise_name', '') if is_franchise else 'Admin',
        }

    def get_object(self, pk):
        try:
            return Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            return None

    # ✅ GET - Single
    def get(self, request, pk):
        user = request.user
        ctx = self.get_franchise_context(user)

        student = self.get_object(pk)
        if not student:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔒 Franchise sirf apna record dekh sakta hai
        if ctx['is_franchise']:
            if student.franchise_code != ctx['franchise_code']:
                return Response(
                    {"error": "Access denied. This record does not belong to you."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = StudentSerializer(student)
        return Response(serializer.data)

    # ✅ PUT - Update
    def put(self, request, pk):
        user = request.user
        ctx = self.get_franchise_context(user)

        student = self.get_object(pk)
        if not student:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔒 Franchise sirf apna record update kar sakta hai
        if ctx['is_franchise']:
            if student.franchise_code != ctx['franchise_code']:
                return Response(
                    {"error": "Access denied. You can only update your own records."},
                    status=status.HTTP_403_FORBIDDEN
                )

        data = request.data.copy()

        # 🔒 Franchise apna code change nahi kar sakta
        if ctx['is_franchise']:
            data['franchise_code'] = ctx['franchise_code']
            data['franchise_name'] = ctx['franchise_name']

        serializer = StudentSerializer(student, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Student updated successfully",
                "data": serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ✅ DELETE - Soft Delete with Franchise Check
    def delete(self, request, pk):
        user = request.user
        ctx = self.get_franchise_context(user)

        student = self.get_object(pk)
        if not student:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔒 Franchise sirf apna record delete kar sakta hai
        if ctx['is_franchise']:
            if student.franchise_code != ctx['franchise_code']:
                return Response(
                    {"error": "Access denied. You can only delete your own records."},
                    status=status.HTTP_403_FORBIDDEN
                )

        student.status = 'Inactive'
        student.save()
        return Response(
            {"message": "Student deleted successfully"},
            status=status.HTTP_200_OK
        )


# ============================================
# 💳 PAYMENT VIEWS - FRANCHISE SAFE
# ============================================

class PaymentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_franchise_context(self, user):
        is_franchise = hasattr(user, 'role') and user.role == 'franchise'
        return {
            'is_franchise': is_franchise,
            'franchise_code': getattr(user, 'franchise_code', '') if is_franchise else None,
            'franchise_name': getattr(user, 'franchise_name', '') if is_franchise else 'Admin',
        }

    # ✅ GET - List
    def get(self, request):
        user = request.user
        ctx = self.get_franchise_context(user)

        queryset = Payment.objects.all()

        if ctx['is_franchise']:
            # 🔒 Franchise → sirf apna data
            queryset = queryset.filter(franchise_code=ctx['franchise_code'])
        else:
            # ✅ Admin → sirf apna (empty franchise_code)
            queryset = queryset.filter(
                Q(franchise_code__isnull=True) | Q(franchise_code='')
            )

        serializer = PaymentSerializer(queryset.order_by('-created_at'), many=True)
        return Response(serializer.data)

    # ✅ POST - Create
    def post(self, request):
        data = request.data.copy()
        user = request.user
        ctx = self.get_franchise_context(user)

        if ctx['is_franchise']:
            data['franchise_code'] = ctx['franchise_code']
            data['franchise_name'] = ctx['franchise_name']
            data['created_by'] = user.username
        else:
            data['franchise_code'] = ''
            data['franchise_name'] = 'Admin'
            data['created_by'] = 'admin'

        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Payment added successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_franchise_context(self, user):
        is_franchise = hasattr(user, 'role') and user.role == 'franchise'
        return {
            'is_franchise': is_franchise,
            'franchise_code': getattr(user, 'franchise_code', '') if is_franchise else None,
            'franchise_name': getattr(user, 'franchise_name', '') if is_franchise else 'Admin',
        }

    def get_object(self, pk):
        try:
            return Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            return None

    # ✅ GET - Single
    def get(self, request, pk):
        user = request.user
        ctx = self.get_franchise_context(user)

        payment = self.get_object(pk)
        if not payment:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔒 Franchise sirf apna payment dekh sakta hai
        if ctx['is_franchise']:
            if payment.franchise_code != ctx['franchise_code']:
                return Response(
                    {"error": "Access denied. This payment does not belong to you."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = PaymentSerializer(payment)
        return Response(serializer.data)

    # ✅ PUT - Update
    def put(self, request, pk):
        user = request.user
        ctx = self.get_franchise_context(user)

        payment = self.get_object(pk)
        if not payment:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔒 Franchise sirf apna payment update kar sakta hai
        if ctx['is_franchise']:
            if payment.franchise_code != ctx['franchise_code']:
                return Response(
                    {"error": "Access denied. You can only update your own payments."},
                    status=status.HTTP_403_FORBIDDEN
                )

        data = request.data.copy()

        # 🔒 Franchise apna code change nahi kar sakta
        if ctx['is_franchise']:
            data['franchise_code'] = ctx['franchise_code']
            data['franchise_name'] = ctx['franchise_name']

        serializer = PaymentSerializer(payment, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Payment updated successfully",
                "data": serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ✅ DELETE
    def delete(self, request, pk):
        user = request.user
        ctx = self.get_franchise_context(user)

        payment = self.get_object(pk)
        if not payment:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔒 Franchise sirf apna payment delete kar sakta hai
        if ctx['is_franchise']:
            if payment.franchise_code != ctx['franchise_code']:
                return Response(
                    {"error": "Access denied. You can only delete your own payments."},
                    status=status.HTTP_403_FORBIDDEN
                )

        payment.delete()
        return Response(
            {"message": "Payment deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
# ============================================
# 🔧 VOCATIONAL STUDENT VIEWS (Updated)
# ============================================
class VocationalStudentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # GET - List + Single
    def get(self, request, pk=None):
        # Single Record
        if pk:
            try:
                student = VocationalStudent.objects.get(pk=pk)
            except VocationalStudent.DoesNotExist:
                return Response(
                    {"error": "Student not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = VocationalStudentSerializer(student)
            return Response(serializer.data)

        # All Records with Franchise Filter
        user = request.user
        queryset = VocationalStudent.objects.all()

        if hasattr(user, 'role') and user.role == 'franchise':
            queryset = queryset.filter(franchise_code=user.franchise_code)
        else:
            # Admin → sirf un records jo franchise_code empty hain
            queryset = queryset.filter(
                Q(franchise_code__isnull=True) | Q(franchise_code='')
            )

        serializer = VocationalStudentSerializer(queryset.order_by('-created_at'), many=True)
        return Response(serializer.data)

    # POST - Create
    def post(self, request):
        data = request.data.copy()
        user = request.user

        if hasattr(user, 'role') and user.role == 'franchise':
            data['franchise_code'] = user.franchise_code
            data['franchise_name'] = getattr(user, 'franchise_name', '')
            data['created_by'] = user.username
        else:
            data['franchise_code'] = ''
            data['franchise_name'] = 'Admin'
            data['created_by'] = 'admin'

        serializer = VocationalStudentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Vocational student added successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # PUT - Update
    def put(self, request, pk):
        try:
            student = VocationalStudent.objects.get(pk=pk)
        except VocationalStudent.DoesNotExist:
            return Response(
                {"error": "Student not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = VocationalStudentSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Vocational student updated successfully",
                "data": serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    def delete(self, request, pk):
        try:
            student = VocationalStudent.objects.get(pk=pk)
        except VocationalStudent.DoesNotExist:
            return Response(
                {"error": "Student not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        student.delete()
        return Response(
            {"message": "Vocational student deleted successfully"}, 
            status=status.HTTP_204_NO_CONTENT
        )

# ============================================
# 💳 VOCATIONAL PAYMENT VIEWS - FRANCHISE SAFE
# ============================================
class VocationalPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_franchise_context(self, user):
        is_franchise = hasattr(user, 'role') and user.role == 'franchise'
        return {
            'is_franchise': is_franchise,
            'franchise_code': getattr(user, 'franchise_code', '') if is_franchise else None,
            'franchise_name': getattr(user, 'franchise_name', '') if is_franchise else 'Admin',
        }

    def get(self, request, pk=None):
        user = request.user
        ctx = self.get_franchise_context(user)

        if pk:
            try:
                payment = VocationalPayment.objects.get(pk=pk)
            except VocationalPayment.DoesNotExist:
                return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

            if ctx['is_franchise'] and payment.franchise_code != ctx['franchise_code']:
                return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

            serializer = VocationalPaymentSerializer(payment)
            return Response(serializer.data)

        queryset = VocationalPayment.objects.all()
        if ctx['is_franchise']:
            queryset = queryset.filter(franchise_code=ctx['franchise_code'])
        else:
            queryset = queryset.filter(Q(franchise_code__isnull=True) | Q(franchise_code=''))

        serializer = VocationalPaymentSerializer(queryset.order_by('-created_at'), many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        user = request.user
        ctx = self.get_franchise_context(user)

        if ctx['is_franchise']:
            data['franchise_code'] = ctx['franchise_code']
            data['franchise_name'] = ctx['franchise_name']
            data['created_by'] = user.username
        else:
            data['franchise_code'] = ''
            data['franchise_name'] = 'Admin'
            data['created_by'] = 'admin'

        serializer = VocationalPaymentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Payment added successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        user = request.user
        ctx = self.get_franchise_context(user)

        try:
            payment = VocationalPayment.objects.get(pk=pk)
        except VocationalPayment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if ctx['is_franchise'] and payment.franchise_code != ctx['franchise_code']:
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        if ctx['is_franchise']:
            data['franchise_code'] = ctx['franchise_code']
            data['franchise_name'] = ctx['franchise_name']

        serializer = VocationalPaymentSerializer(payment, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Payment updated successfully", "data": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = request.user
        ctx = self.get_franchise_context(user)

        try:
            payment = VocationalPayment.objects.get(pk=pk)
        except VocationalPayment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if ctx['is_franchise'] and payment.franchise_code != ctx['franchise_code']:
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        payment.delete()
        return Response({"message": "Payment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


    
# ============================================
# 📤 FRANCHISE APPLICANTS VIEW
# ============================================


class FranchiseApplicantsView(APIView):
    """
    GET: Get all applicants for a franchise
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            franchise = Franchise.objects.get(pk=pk)
        except Franchise.DoesNotExist:
            return Response(
                {'error': 'Franchise not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        applicants = Applicant.objects.filter(franchise=franchise, is_active=True)
        serializer = ApplicantSerializer(applicants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ============================================
# 🔑 FRANCHISE PASSWORD CHANGE
# ============================================
class FranchisePasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        old_password = request.data.get('old_password', '').strip()
        new_password = request.data.get('new_password', '').strip()
        
        # Validation
        if not old_password or not new_password:
            return Response({
                'status': 'error',
                'message': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Current password sahi hai?
        if not user.check_password(old_password):
            return Response({
                'status': 'error',
                'message': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Minimum length
        if len(new_password) < 6:
            return Response({
                'status': 'error',
                'message': 'Password must be at least 6 characters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Same password check
        if old_password == new_password:
            return Response({
                'status': 'error',
                'message': 'New password must be different'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ✅ Sirf password change - baaki sab same
        user.set_password(new_password)
        user.save()
        
        print(f"✅ Password changed: {user.username}")
        
        return Response({
            'status': 'success',
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
# ============================================
# 🌐 WEBSITE CATEGORY VIEWS
# ============================================
class CourseCategoryListCreateView(APIView):
    def get(self, request):
        data = CourseCategory.objects.all()
        serializer = CourseCategorySerializer(data, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CourseCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseCategoryDetailView(APIView):
    def delete(self, request, pk):
        obj = get_object_or_404(CourseCategory, pk=pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# 🌐 WEBSITE DURATION VIEWS
# ============================================
class CourseDurationListCreateView(APIView):
    def get(self, request):
        data = CourseDuration.objects.all()
        serializer = CourseDurationSerializer(data, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CourseDurationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseDurationDetailView(APIView):
    def delete(self, request, pk):
        obj = get_object_or_404(CourseDuration, pk=pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# 🌐 WEBSITE COURSE VIEWS
# ============================================
class WebsiteCourseListCreateView(APIView):
    def get(self, request):
        data = WebsiteCourse.objects.filter(is_active=True)
        serializer = WebsiteCourseSerializer(data, many=True)
        return Response(serializer.data)

    def post(self, request):
        import time
        from django.utils.text import slugify
        data = request.data.copy()

        # ✅ Slug auto generate — unique timestamp ke saath
        if data.get('name'):
            data['slug'] = f"{slugify(data['name'])}-{int(time.time())}"

        # ✅ Image blank ho toh field hi remove karo
        if not data.get('image') or str(data.get('image')).strip() == '':
            data.pop('image', None)

        serializer = WebsiteCourseSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print("❌ COURSE ERROR:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebsiteCourseDetailView(APIView):
    def get(self, request, pk):
        obj = get_object_or_404(WebsiteCourse, pk=pk)
        serializer = WebsiteCourseSerializer(obj)
        return Response(serializer.data)

    def put(self, request, pk):
        obj = get_object_or_404(WebsiteCourse, pk=pk)
        data = request.data.copy()

        # ✅ Image blank ho toh field remove karo
        if not data.get('image') or str(data.get('image')).strip() == '':
            data.pop('image', None)

        # ✅ Slug existing rakho
        if not data.get('slug'):
            data['slug'] = obj.slug

        serializer = WebsiteCourseSerializer(obj, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        print("❌ UPDATE ERROR:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = get_object_or_404(WebsiteCourse, pk=pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# 🌐 WEBSITE ENQUIRY VIEWS
# ============================================
class WebsiteEnquiryListCreateView(APIView):
    def get(self, request):
        data = WebsiteEnquiry.objects.all()
        serializer = WebsiteEnquirySerializer(data, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WebsiteEnquirySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print("❌ ENQUIRY ERROR:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebsiteEnquiryDetailView(APIView):
    def get(self, request, pk):
        obj = get_object_or_404(WebsiteEnquiry, pk=pk)
        serializer = WebsiteEnquirySerializer(obj)
        return Response(serializer.data)

    def patch(self, request, pk):
        obj = get_object_or_404(WebsiteEnquiry, pk=pk)
        serializer = WebsiteEnquirySerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        print("❌ ENQUIRY UPDATE ERROR:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = get_object_or_404(WebsiteEnquiry, pk=pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




     # **********************************
            #    paymet rozay pay
    # *****************************************************
    
    # ============================================
# 💰 WALLET VIEWS - Simple Class Based
# ============================================




# ============================================
# 1️⃣ WALLET BALANCE - GET
# ============================================
class WalletBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        show_all = request.query_params.get('all')

        # Admin: Sab wallets
        if show_all and getattr(user, 'role', '') != 'franchise':
            wallets = CertificateWallet.objects.all()
            serializer = CertificateWalletSerializer(wallets, many=True)
            return Response(serializer.data)

        # Franchise: Apna wallet
        if getattr(user, 'role', '') == 'franchise':
            franchise_code = getattr(user, 'franchise_code', '')

            if not franchise_code:
                return Response({'wallet': None})

            wallet, created = CertificateWallet.objects.get_or_create(
                franchise_code=franchise_code,
                defaults={
                    'franchise_name': getattr(user, 'franchise_name', '')
                }
            )

            serializer = CertificateWalletSerializer(wallet)
            return Response({'wallet': serializer.data})

        return Response({'wallet': None})

# ============================================
# 2️⃣ PACKAGE LIST + CREATE (Course Based)
# ============================================
class PackageListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    # GET: Sab courses
    def get(self, request):
        packages = CertificatePackage.objects.filter(
            status='active'
        )
        serializer = CertificatePackageSerializer(
            packages, many=True
        )
        return Response(serializer.data)

    # POST: Naya course package banao (admin only)
    def post(self, request):
        if getattr(request.user, 'role', '') == 'franchise':
            return Response(
                {'error': 'Only admin can create courses'},
                status=403
            )

        data = request.data.copy()

        # ✅ Course name set karo (agar name field diya hai)
        if not data.get('course_name') and data.get('name'):
            data['course_name'] = data['name']
        elif not data.get('name') and data.get('course_name'):
            data['name'] = data['course_name']

        # Auto calculate per cert price
        try:
            cert_count = int(data.get('certificate_count', 0))
            price = float(data.get('price', 0))
            if cert_count > 0:
                data['per_certificate_price'] = price / cert_count
        except (ValueError, ZeroDivisionError):
            pass

        serializer = CertificatePackageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)

    # ============================================
# 3️⃣ PACKAGE UPDATE + DELETE (Course Based)
# ============================================
class PackageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        if getattr(request.user, 'role', '') == 'franchise':
            return Response({'error': 'Not allowed'}, status=403)

        try:
            pkg = CertificatePackage.objects.get(id=pk)
        except CertificatePackage.DoesNotExist:
            return Response(
                {'error': 'Course not found'}, status=404
            )

        data = request.data.copy()

        # ✅ Course name sync
        if not data.get('course_name') and data.get('name'):
            data['course_name'] = data['name']
        elif not data.get('name') and data.get('course_name'):
            data['name'] = data['course_name']

        try:
            cert_count = int(
                data.get('certificate_count', pkg.certificate_count)
            )
            price = float(data.get('price', pkg.price))
            if cert_count > 0:
                data['per_certificate_price'] = price / cert_count
        except (ValueError, ZeroDivisionError):
            pass

        serializer = CertificatePackageSerializer(
            pkg, data=data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        if getattr(request.user, 'role', '') == 'franchise':
            return Response({'error': 'Not allowed'}, status=403)

        try:
            pkg = CertificatePackage.objects.get(id=pk)
            pkg.delete()
            return Response({'message': 'Course deleted'}, status=204)
        except CertificatePackage.DoesNotExist:
            return Response(
                {'error': 'Course not found'}, status=404
            )
        
# ============================================
# 4️⃣ TRANSACTION LIST
# ============================================
class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Franchise: Apne transactions
        if getattr(user, 'role', '') == 'franchise':
            txns = WalletTransaction.objects.filter(
                franchise_code=user.franchise_code
            )
        else:
            # Admin: Sab ya filter
            franchise_code = request.query_params.get('franchise_code')
            if franchise_code:
                txns = WalletTransaction.objects.filter(
                    franchise_code=franchise_code
                )
            else:
                txns = WalletTransaction.objects.all()

        serializer = WalletTransactionSerializer(txns, many=True)
        return Response(serializer.data)


# ============================================
# 5️⃣ ADMIN ASSIGN COURSE PACKAGE
# ============================================
class WalletPurchaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Only admin
        if getattr(request.user, 'role', '') == 'franchise':
            return Response(
                {'error': 'Only admin can assign'},
                status=403
            )

        franchise_code = request.data.get('franchise_code')
        franchise_name = request.data.get('franchise_name', '')
        package_id = request.data.get('package_id')
        payment_method = request.data.get(
            'payment_method', 'cash'
        )
        payment_reference = request.data.get(
            'payment_reference', ''
        )

        if not franchise_code or not package_id:
            return Response(
                {'error': 'franchise_code and package_id required'},
                status=400
            )

        try:
            pkg = CertificatePackage.objects.get(
                id=package_id, status='active'
            )
        except CertificatePackage.DoesNotExist:
            return Response(
                {'error': 'Course not found'}, status=404
            )

        # ✅ Course name nikaalo
        course_name = pkg.course_name or pkg.name

        # Get or create wallet
        wallet, created = CertificateWallet.objects.get_or_create(
            franchise_code=franchise_code,
            defaults={'franchise_name': franchise_name}
        )

        balance_before = wallet.remaining_certificates

        # Add certificates
        wallet.add_certificates(
            count=pkg.certificate_count,
            amount=Decimal(str(pkg.price))
        )

        # ✅ Transaction record with course_name
        WalletTransaction.objects.create(
            wallet=wallet,
            package=pkg,
            transaction_type='admin_add',
            franchise_code=franchise_code,
            course_name=course_name,  # ✅ NEW
            certificate_count=pkg.certificate_count,
            amount=pkg.price,
            balance_before=balance_before,
            balance_after=wallet.remaining_certificates,
            payment_method=payment_method,
            payment_status='completed',
            payment_reference=payment_reference,
            remarks=f'{course_name} course assigned',
            created_by=request.user.username,
        )

        return Response({
            'message': f'{pkg.certificate_count} {course_name} certificates assigned!',
            'wallet': CertificateWalletSerializer(wallet).data,
        }, status=201)
    
# ============================================
# 6️⃣ RAZORPAY - CREATE ORDER (WITH DEBUG)
# ============================================
class CreateRazorpayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("\n" + "="*60)
        print("🚀 CREATE ORDER API HIT!")
        print(f"   User: {request.user}")
        print(f"   Role: {getattr(request.user, 'role', 'NO ROLE')}")
        print(f"   Data: {request.data}")
        print("="*60)
        
        try:
            import razorpay
            from django.conf import settings

            key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
            key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
            
            print(f"   RAZORPAY_KEY_ID: {key_id}")
            print(f"   RAZORPAY_KEY_SECRET: {'✅ SET' if key_secret else '❌ NOT SET'}")
            
            if not key_id or not key_secret:
                return Response({
                    'error': 'Razorpay keys not configured'
                }, status=500)

            package_id = request.data.get('package_id')
            print(f"   Package ID: {package_id}")

            if not package_id:
                return Response({'error': 'package_id required'}, status=400)

            try:
                pkg = CertificatePackage.objects.get(id=package_id, status='active')
                print(f"   ✅ Package: {pkg.name} - ₹{pkg.price}")
            except CertificatePackage.DoesNotExist:
                return Response({'error': 'Package not found'}, status=404)

            client = razorpay.Client(auth=(key_id, key_secret))
            amount_paisa = int(float(pkg.price) * 100)
            
            print(f"   Amount: ₹{pkg.price} ({amount_paisa} paisa)")
            print(f"   Creating order on Razorpay...")

            order = client.order.create({
                'amount': amount_paisa,
                'currency': 'INR',
                'receipt': f'ORD_{pkg.id}_{request.user.id}'[:40],
                'notes': {
                    'franchise_code': str(getattr(request.user, 'franchise_code', '')),
                    'package_id': str(pkg.id),
                    'package_name': str(pkg.name),
                }
            })
            
            print(f"   ✅ ORDER CREATED: {order['id']}")
            print("="*60 + "\n")

            return Response({
                'success': True,
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'razorpay_key': key_id,
                'package_name': pkg.name,
                'certificate_count': pkg.certificate_count,
            })

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ ERROR: {str(e)}")
            print(f"❌ TRACEBACK:\n{error_trace}")
            print("="*60 + "\n")
            
            return Response({
                'error': str(e),
                'type': type(e).__name__
            }, status=500)

# ============================================
# 7️⃣ RAZORPAY - VERIFY PAYMENT (WITH DEBUG)
# ============================================
class VerifyRazorpayPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 🔥 DEBUG
        print("\n" + "="*60)
        print("🔐 VERIFY PAYMENT API HIT!")
        print(f"   User: {request.user}")
        print(f"   Data: {request.data}")
        print("="*60)
        
        try:
            import razorpay
            from django.conf import settings

            razorpay_order_id = request.data.get('razorpay_order_id')
            razorpay_payment_id = request.data.get('razorpay_payment_id')
            razorpay_signature = request.data.get('razorpay_signature')
            package_id = request.data.get('package_id')

            print(f"   Order ID: {razorpay_order_id}")
            print(f"   Payment ID: {razorpay_payment_id}")
            print(f"   Package ID: {package_id}")

            # Check all fields
            if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, package_id]):
                print("❌ MISSING FIELDS!")
                return Response({
                    'success': False,
                    'error': 'Missing required fields'
                }, status=400)

            # ✅ Verify signature
            key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
            key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)

            client = razorpay.Client(auth=(key_id, key_secret))

            try:
                client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature,
                })
                print("   ✅ Signature verified!")
            except Exception as e:
                print(f"❌ SIGNATURE VERIFICATION FAILED: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'Payment signature verification failed'
                }, status=400)

            # ✅ Get package
            try:
                pkg = CertificatePackage.objects.get(id=package_id)
                print(f"   ✅ Package: {pkg.name}")
            except CertificatePackage.DoesNotExist:
                print("❌ PACKAGE NOT FOUND!")
                return Response({'error': 'Package not found'}, status=404)

            # ✅ User info
            user = request.user
            franchise_code = getattr(user, 'franchise_code', '')
            franchise_name = getattr(user, 'franchise_name', '')
            
            print(f"   Franchise: {franchise_code}")

            # ✅ Get or create wallet
            wallet, created = CertificateWallet.objects.get_or_create(
                franchise_code=franchise_code,
                defaults={'franchise_name': franchise_name}
            )

            balance_before = wallet.remaining_certificates
            print(f"   Balance BEFORE: {balance_before}")

            # ✅ Add certificates
            wallet.add_certificates(
                count=pkg.certificate_count,
                amount=Decimal(str(pkg.price))
            )
            
            print(f"   ✅ Balance AFTER: {wallet.remaining_certificates}")

            # ✅ Transaction record
            WalletTransaction.objects.create(
                wallet=wallet,
                package=pkg,
                transaction_type='purchase',
                franchise_code=franchise_code,
                certificate_count=pkg.certificate_count,
                amount=pkg.price,
                balance_before=balance_before,
                balance_after=wallet.remaining_certificates,
                payment_method='razorpay',
                payment_status='completed',
                payment_reference=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
                remarks=f'{pkg.name} via Razorpay',
                created_by=user.username,
            )
            
            print(f"   ✅ Transaction record created")
            print("="*60 + "\n")

            return Response({
                'success': True,
                'message': f'{pkg.certificate_count} Certificates added!',
                'new_balance': wallet.remaining_certificates,
                'payment_id': razorpay_payment_id,
            })

        except Exception as e:
            import traceback
            print(f"❌ EXCEPTION: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'success': False,
                'error': f'Server error: {str(e)}'
            }, status=500)



# ============================================
# 8️⃣ CERTIFICATE LIST + CREATE (NO WALLET DEDUCT ON CREATE)
# ============================================

class StudentCertificateListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    # GET: List certificates
    def get(self, request):
        user = request.user
        queryset = StudentCertificate.objects.all()

        # ✅ Franchise → sirf apna data
        if getattr(user, 'role', '') == 'franchise':
            queryset = queryset.filter(franchise_code=user.franchise_code)

        # ✅ Admin → sirf apna data (empty franchise_code)
        else:
            queryset = queryset.filter(
                Q(franchise_code__isnull=True) | Q(franchise_code='')
            )

        # Search
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(student_name__icontains=search) |
                Q(course_name__icontains=search) |
                Q(cert_no__icontains=search) |
                Q(father_name__icontains=search)
            )

        # Type filter
        student_type = request.query_params.get('student_type')
        if student_type:
            queryset = queryset.filter(student_type=student_type)

        serializer = StudentCertificateSerializer(
            queryset.order_by('-created_at'),
            many=True
        )
        return Response(serializer.data)

    # POST: Create certificate
    def post(self, request):
        data = request.data.copy()
        user = request.user

        # ✅ FRANCHISE
        if getattr(user, 'role', '') == 'franchise':
            franchise_code = user.franchise_code
            data['franchise_code'] = franchise_code
            data['franchise_name'] = getattr(user, 'franchise_name', '')
            data['created_by'] = user.username

            # wallet display only
            wallet = CertificateWallet.objects.filter(
                franchise_code=franchise_code
            ).first()
            wallet_remaining = wallet.remaining_certificates if wallet else 0

            serializer = StudentCertificateSerializer(data=data)
            if serializer.is_valid():
                certificate = serializer.save()
                return Response({
                    'message': 'Certificate Saved Successfully!',
                    'data': StudentCertificateSerializer(certificate).data,
                    'wallet_remaining': wallet_remaining,
                }, status=201)

            return Response(serializer.errors, status=400)

        # ✅ ADMIN
        else:
            data['franchise_code'] = ''
            data['franchise_name'] = 'Admin'
            data['created_by'] = 'admin'

            serializer = StudentCertificateSerializer(data=data)
            if serializer.is_valid():
                certificate = serializer.save()
                return Response({
                    'message': 'Certificate Generated Successfully!',
                    'data': StudentCertificateSerializer(certificate).data,
                }, status=201)

            return Response(serializer.errors, status=400)
# ============================================
# 9️⃣ CERTIFICATE DETAIL
# ============================================
class StudentCertificateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_franchise_context(self, user):
        is_franchise = hasattr(user, 'role') and user.role == 'franchise'
        return {
            'is_franchise': is_franchise,
            'franchise_code': getattr(user, 'franchise_code', '') if is_franchise else None,
            'franchise_name': getattr(user, 'franchise_name', '') if is_franchise else 'Admin',
        }

    def get_object(self, pk):
        try:
            return StudentCertificate.objects.get(id=pk)
        except StudentCertificate.DoesNotExist:
            return None

    def get(self, request, pk):
        cert = self.get_object(pk)
        if not cert:
            return Response(
                {'error': 'Certificate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        user = request.user
        ctx = self.get_franchise_context(user)

        if ctx['is_franchise']:
            if cert.franchise_code != ctx['franchise_code']:
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = StudentCertificateSerializer(cert)
        return Response(serializer.data)

    def put(self, request, pk):
        cert = self.get_object(pk)
        if not cert:
            return Response(
                {'error': 'Certificate not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        ctx = self.get_franchise_context(user)

        if ctx['is_franchise']:
            if cert.franchise_code != ctx['franchise_code']:
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

        data = request.data.copy()
        if ctx['is_franchise']:
            data['franchise_code'] = ctx['franchise_code']
            data['franchise_name'] = ctx['franchise_name']

        serializer = StudentCertificateSerializer(
            cert, data=data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Certificate Updated!',
                'data': serializer.data,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        cert = self.get_object(pk)
        if not cert:
            return Response(
                {'error': 'Certificate not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        ctx = self.get_franchise_context(user)

        if ctx['is_franchise']:
            if cert.franchise_code != ctx['franchise_code']:
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

        cert_no = cert.cert_no
        cert.delete()

        return Response({
            'message': f'Certificate {cert_no} Deleted!'
        }, status=status.HTTP_204_NO_CONTENT)
# ============================================
# 🔟 CERTIFICATE STATS
# ============================================
class StudentCertificateStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        queryset = StudentCertificate.objects.all()

        if hasattr(user, 'role') and user.role == 'franchise':
            queryset = queryset.filter(
                franchise_code=user.franchise_code
            )
        else:
            # Admin → sirf apna
            queryset = queryset.filter(
                Q(franchise_code__isnull=True) | Q(franchise_code='')
            )

        return Response({
            'total': queryset.count(),
            'student': queryset.filter(
                student_type='student'
            ).count(),
            'vocational': queryset.filter(
                student_type='vocational'
            ).count(),
            'downloaded': queryset.filter(
                is_downloaded=True
            ).count(),
        })
# ============================================
# 1️⃣1️⃣ MARK DOWNLOADED - Course Wise Deduction
# ============================================
class MarkCertificateDownloadedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        print("\n" + "="*60)
        print("🔥 DOWNLOAD API HIT!")
        print(f"   Cert ID: {pk}")
        print(f"   User: {request.user}")
        print("="*60)

        try:
            cert = StudentCertificate.objects.get(id=pk)
        except StudentCertificate.DoesNotExist:
            return Response(
                {'error': 'Certificate not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        # Franchise check
        is_franchise = (
            hasattr(user, 'role') and user.role == 'franchise'
        )

        if is_franchise:
            if cert.franchise_code != user.franchise_code:
                return Response(
                    {'error': 'Access denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # ✅ Course name from certificate
        cert_course = cert.course_name or 'Unknown'
        print(f"   Course: {cert_course}")
        print(f"   wallet_deducted: {cert.wallet_deducted}")

        is_first_download = not cert.wallet_deducted
        wallet_deducted_now = False
        wallet_remaining = None
        course_balance = None

        # ✅ SIRF FRANCHISE ke liye wallet deduct
        # ✅ SIRF FIRST DOWNLOAD pe deduct
        if is_franchise and is_first_download and cert.franchise_code:
            wallet = CertificateWallet.objects.filter(
                franchise_code=cert.franchise_code
            ).first()

            if not wallet:
                return Response({
                    'error': 'Wallet not found',
                    'message': 'Please contact admin.'
                }, status=404)

            # ✅ Course wise balance check
            course_bal = wallet.get_course_balance(cert_course)
            print(f"   Course Balance: {course_bal}")

            if course_bal['remaining'] <= 0:
                return Response({
                    'error': f'No balance for {cert_course}!',
                    'course': cert_course,
                    'remaining': 0,
                    'message': f'Please recharge {cert_course} course.'
                }, status=400)

            # ✅ DEDUCT
            balance_before = wallet.remaining_certificates
            wallet.remaining_certificates -= 1
            wallet.used_certificates = (
                wallet.used_certificates or 0
            ) + 1
            wallet.save()

            print(f"✅ WALLET DEDUCTED for {cert_course}!")
            print(f"   Remaining AFTER: {wallet.remaining_certificates}")

            # ✅ Transaction with course_name
            WalletTransaction.objects.create(
                wallet=wallet,
                certificate=cert,
                transaction_type='deduction',
                franchise_code=cert.franchise_code,
                course_name=cert_course,  # ✅ NEW
                certificate_count=1,
                amount=0,
                balance_before=balance_before,
                balance_after=wallet.remaining_certificates,
                remarks=f'{cert_course}: {cert.student_name} ({cert.cert_no})',
                created_by=getattr(user, 'username', 'system'),
            )

            wallet_deducted_now = True
            wallet_remaining = wallet.remaining_certificates

            # Updated course balance
            course_balance = wallet.get_course_balance(cert_course)

        elif is_franchise and not is_first_download and cert.franchise_code:
            print("⏭️ ALREADY DEDUCTED")
            wallet = CertificateWallet.objects.filter(
                franchise_code=cert.franchise_code
            ).first()
            if wallet:
                wallet_remaining = wallet.remaining_certificates
                course_balance = wallet.get_course_balance(
                    cert_course
                )

        # ✅ Mark downloaded
        cert.is_downloaded = True
        cert.download_count = (cert.download_count or 0) + 1

        if wallet_deducted_now:
            cert.wallet_deducted = True

        cert.save(update_fields=[
            'is_downloaded', 'download_count', 'wallet_deducted'
        ])

        print("="*60 + "\n")

        return Response({
            'success': True,
            'message': 'Certificate downloaded successfully',
            'cert_no': cert.cert_no,
            'course_name': cert_course,
            'download_count': cert.download_count,
            'wallet_deducted': wallet_deducted_now,
            'wallet_remaining': wallet_remaining,
            'course_balance': course_balance,
            'is_first_download': is_first_download,
        }, status=200)