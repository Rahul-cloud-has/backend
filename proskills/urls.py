# proskills/urls.py - FINAL COMPLETE FILE

from django.urls import path
from . import views
from .views import FranchisePasswordChangeView  # ← YE ADD KARO


urlpatterns = [

    # ============================================
    # 🔐 LOGIN
    # ============================================
    path('login/', views.LoginView.as_view(), name='login'),

    # ============================================
    # 📚 CATEGORIES
    # ============================================
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),

    # ============================================
    # 📚 SESSIONS
    # ============================================
    path('sessions/', views.SessionListCreateView.as_view(), name='session-list-create'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session-detail'),

    # ============================================
    # 📚 COURSES
    # ============================================
    path('courses/', views.CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course-detail'),

    # ============================================
    # 💼 JOBS
    # ============================================
    path('jobs/', views.JobListCreateView.as_view(), name='job-list-create'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),

    # ============================================
    # 💳 FRANCHISE PAYMENTS
    # ============================================
    path('franchise-payments/', views.FranchisePaymentListCreateView.as_view(), name='franchise-payment-list-create'),
    path('franchise-payments/<int:pk>/', views.FranchisePaymentDetailView.as_view(), name='franchise-payment-detail'),
# 👨‍🎓 STUDENTS
# ============================================
path('students/', views.StudentListCreateView.as_view(), name='student-list-create'),
path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student-detail'),

# ============================================
# 💳 PAYMENTS
# ============================================
path('payments/', views.PaymentListCreateView.as_view(), name='payment-list-create'),
path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),

    # ============================================
    # 🔧 VOCATIONAL STUDENTS
    # ============================================
    path('vocational/students/', views.VocationalStudentAPIView.as_view(), name='vocational-student-list'),
    path('vocational/students/<int:pk>/', views.VocationalStudentAPIView.as_view(), name='vocational-student-detail'),

    # ============================================
    # 💳 VOCATIONAL PAYMENTS
    # ============================================
    path('vocational/payments/', views.VocationalPaymentAPIView.as_view(), name='vocational-payment-list'),
    path('vocational/payments/<int:pk>/', views.VocationalPaymentAPIView.as_view(), name='vocational-payment-detail'),

    # ============================================
    # 📝 APPLICATIONS
    # ============================================
    path('applications/', views.ApplicationListCreateView.as_view(), name='application-list'),
    path('applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application-detail'),
    path('applications/<int:pk>/status/', views.ApplicationStatusUpdateView.as_view(), name='application-status'),

    # ============================================
    # 🏢 GENERATED FRANCHISES
    # ============================================
    path('generated-franchises/', views.GeneratedFranchiseListCreateView.as_view(), name='generated-franchise-list'),
    path('generated-franchises/<int:pk>/', views.GeneratedFranchiseDetailView.as_view(), name='generated-franchise-detail'),

    # ============================================
    # 🏢 FRANCHISE
    # ============================================
    path('franchises/', views.FranchiseListCreateView.as_view(), name='franchise-list'),
    path('franchises/<int:pk>/', views.FranchiseDetailView.as_view(), name='franchise-detail'),
    path('franchises/<int:pk>/applicants/', views.FranchiseApplicantsView.as_view(), name='franchise-applicants'),

    # ============================================
    # 👤 APPLICANTS
    # ============================================
    path('applicants/', views.ApplicantListCreateView.as_view(), name='applicant-list'),
    path('applicants/<int:pk>/', views.ApplicantDetailView.as_view(), name='applicant-detail'),

    # ============================================
    # 👥 FRANCHISE USERS
    # ============================================
    path('franchise-users/stats/', views.FranchiseUserStatsView.as_view(), name='franchise-user-stats'),
    path('franchise-users/', views.FranchiseUserListCreateView.as_view(), name='franchise-user-list'),
    path('franchise-users/<int:pk>/', views.FranchiseUserDetailView.as_view(), name='franchise-user-detail'),

    # ============================================
    # 🔐 PERMISSIONS
    # ============================================
    path('permissions/all/', views.AllPermissionsView.as_view(), name='all-permissions'),
    path('permissions/bulk-update/', views.BulkPermissionUpdateView.as_view(), name='bulk-permission-update'),
    path('permissions/<int:user_id>/', views.UserPermissionsView.as_view(), name='user-permissions'),
    path('permissions/<int:user_id>/update/', views.UserPermissionUpdateView.as_view(), name='update-permissions'),

    # ============================================
    # 📊 USER PROFILE
    # ============================================
    path('user/profile/', views.UserProfileView.as_view(), name='user-profile'),

    # ============================================
    # 📜 FRANCHISE CERTIFICATES
    # ============================================
    path('franchise-certificates/', views.FranchiseCertificateListCreateView.as_view(), name='franchise-certificate-list'),
    path('franchise-certificates/stats/', views.FranchiseCertificateStatsView.as_view(), name='franchise-certificate-stats'),
    path('franchise-certificates/by-franchise/', views.FranchiseCertificateByFranchiseView.as_view(), name='franchise-certificate-by-franchise'),
    path('franchise-certificates/<int:pk>/', views.FranchiseCertificateDetailView.as_view(), name='franchise-certificate-detail'),

   # ============================================
# 📜 STUDENT CERTIFICATES
# ============================================
path('student-certificates/', views.StudentCertificateListCreateView.as_view(), name='student-certificate-list'),
path('student-certificates/stats/', views.StudentCertificateStatsView.as_view(), name='student-certificate-stats'),
path('student-certificates/<int:pk>/', views.StudentCertificateDetailView.as_view(), name='student-certificate-detail'),
path('student-certificates/<int:pk>/download/', views.MarkCertificateDownloadedView.as_view(), name='student-certificate-download'),


   # ✅ Ye add karo
    path('franchise/change-password/', FranchisePasswordChangeView.as_view()),

        # ============================================
    # 🌐 WEBSITE CATEGORIES
    # ============================================
    path('website/categories/', views.CourseCategoryListCreateView.as_view(), name='website-category-list'),
    path('website/categories/<int:pk>/', views.CourseCategoryDetailView.as_view(), name='website-category-detail'),

    # ============================================
    # 🌐 WEBSITE DURATIONS
    # ============================================
    path('website/durations/', views.CourseDurationListCreateView.as_view(), name='website-duration-list'),
    path('website/durations/<int:pk>/', views.CourseDurationDetailView.as_view(), name='website-duration-detail'),

    # ============================================
    # 🌐 WEBSITE COURSES
    # ============================================
    path('website/courses/', views.WebsiteCourseListCreateView.as_view(), name='website-course-list'),
    path('website/courses/<int:pk>/', views.WebsiteCourseDetailView.as_view(), name='website-course-detail'),

    # ============================================
    # 🌐 WEBSITE ENQUIRIES
    # ============================================
    path('website/enquiries/', views.WebsiteEnquiryListCreateView.as_view(), name='website-enquiry-list'),
    path('website/enquiries/<int:pk>/', views.WebsiteEnquiryDetailView.as_view(), name='website-enquiry-detail'),

        # ============================================
    # 💰 WALLET SYSTEM
    # ============================================
    path('wallet/balance/', views.WalletBalanceView.as_view(), name='wallet-balance'),
    path('wallet/packages/', views.PackageListCreateView.as_view(), name='wallet-packages'),
    path('wallet/packages/<int:pk>/', views.PackageDetailView.as_view(), name='wallet-package-detail'),
    path('wallet/transactions/', views.TransactionListView.as_view(), name='wallet-transactions'),
    path('wallet/purchase/', views.WalletPurchaseView.as_view(), name='wallet-purchase'),

    # ============================================
    # 💳 RAZORPAY
    # ============================================
    path('wallet/create-order/', views.CreateRazorpayOrderView.as_view(), name='wallet-create-order'),
    path('wallet/verify-payment/', views.VerifyRazorpayPaymentView.as_view(), name='wallet-verify-payment'),
]