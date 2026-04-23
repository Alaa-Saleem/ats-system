"""
Script to compile Arabic and English .po files and generate .mo files
without requiring GNU gettext tools.
Run: python compile_translations.py
"""
import struct
import os

ar_translations = {
    # Navigation
    "القائمة الرئيسية": "Main Menu",
    "الرئيسية": "Dashboard",
    "نظام التوظيف": "Recruitment System",
    "المرشحون": "Candidates",
    "الوظائف": "Jobs",
    "العملاء": "Clients",
    "الإعدادات": "Settings",
    "إدارة الفريق": "Team Management",
    "تسجيل الخروج": "Logout",
    "تغيير المظهر": "Toggle Theme",
    "نظام إدارة التوظيف": "Recruitment Management System",
    "ملفي الشخصي": "My Profile",
    # Auth
    "تسجيل الدخول": "Login",
    "البريد الإلكتروني": "Email",
    "كلمة المرور": "Password",
    "تذكرني": "Remember me",
    "سجل كشركة": "Register as Company",
    "سجل كمرشح": "Register as Candidate",
    "ليس لديك حساب؟": "Don't have an account?",
    "لديك حساب؟": "Already have an account?",
    # Jobs
    "الوظائف المتاحة": "Available Jobs",
    "تصفح الوظائف": "Browse Jobs",
    "أضف وظيفة": "Add Job",
    "تعديل الوظيفة": "Edit Job",
    "حالة الوظيفة": "Job Status",
    "مفتوح": "Open",
    "مغلق": "Closed",
    # Candidates
    "المتقدمون": "Applicants",
    "إضافة مرشح": "Add Candidate",
    # Dashboard
    "لوحة التحكم": "Dashboard",
    "إجمالي الوظائف": "Total Jobs",
    "إجمالي المتقدمين": "Total Applicants",
    "التقديمات": "Applications",
    "طلباتي": "My Applications",
    "مستخدم": "User",
    # Common
    "حفظ": "Save",
    "إلغاء": "Cancel",
    "حذف": "Delete",
    "تعديل": "Edit",
    "البحث": "Search",
    "تصفية": "Filter",
    "الكل": "All",
    "لا توجد بيانات": "No data available",
    "نعم": "Yes",
    "لا": "No",

    # NEW: Jobs Applications
    "طلبات التقديم": "Applications",
    "طلبات التقديم:": "Applications:",
    "عودة للوظائف": "Back to Jobs",
    "إجمالي المتقدمين:": "Total Applicants:",
    "عرض في التوظيف": "View in Pipeline",
    "اسم المرشح": "Candidate Name",
    "تاريخ التقديم": "Applied Date",
    "المرحلة الحالية": "Current Stage",
    "المسمى الحالي": "Current Title",
    "الخبرة": "Experience",
    "إجراءات": "Actions",
    "سنوات": "Years",
    "تحميل السيرة الذاتية": "Download CV",
    "لا يوجد طلبات تقديم حتى الآن": "No applications yet",

    # ─── Candidates Page ───
    "إدارة المرشحين": "Candidate Management",
    "المرشحين": "Candidates",
    "استعراض وإدارة قاعدة بيانات المرشحين المحتملين": "Browse and manage potential candidates database",
    "فلترة حسب الوظيفة": "Filter by Job",
    "كل الوظائف": "All Jobs",
    "تطبيق": "Apply",
    "إعادة تعيين": "Reset",
    "المرشح": "Candidate",
    "المسمى الوظيفي": "Job Title",
    "الإجراءات": "Actions",
    "عرض التفاصيل": "View Details",
    "عرض": "View",
    "لا يوجد مرشحين": "No candidates found",
    "لم يتم إضافة أي مرشحين بعد. ابدأ بإضافة مرشحك الأول.": "No candidates added yet. Start by adding your first candidate.",
    "إضافة مرشح جديد": "Add New Candidate",
    "العودة للوراء": "Go Back",
    "بدون عمل": "Unemployed",
    "العودة للقائمة": "Back to List",

    # NEW: Candidate Details
    "بيانات المرشح": "Candidate Details",
    "بيانات عامة": "General Info",
    "الاسم الكامل": "Full Name",
    "رقم الهاتف": "Phone Number",
    "المسمى الوظيفي الحالي": "Current Job Title",
    "سنوات الخبرة": "Years of Experience",
    "الموقع / المدينة": "Location / City",
    "السيرة الذاتية (CV)": "CV / Resume",
    "تحميل الملف": "Download File",
    "ملاحظات إضافية": "Additional Notes",
    "الطلب الحالي": "Current Application",
    "الوظيفة المتقدم لها": "Applied Job",
    "مصدر التقديم": "Application Source",
    "إجابات النموذج الإضافية": "Custom Form Answers",
    "عرض الملف": "View File",
    "لا توجد حقول إضافية ضمن نموذج هذا الطلب.": "No additional fields for this application.",
    "لا يوجد طلب تقديم مرتبط بهذا المرشح حتى الآن.": "No application linked to this candidate yet.",

    # ─── Team Management ───
    "Team Management": "Team Management",
    "إعدادات الفريق": "Team Settings",
    "أضف وأدر أعضاء فريق شركتك وصلاحياتهم": "Add and manage your company team members and their permissions",
    "إضافة عضو": "Add Member",
    "إضافة عضو جديد": "Add New Member",
    "أعضاء الفريق": "Team Members",
    "المستخدم": "User",
    "الدور": "Role",
    "لا يوجد أعضاء فريق": "No team members found",
    "ابدأ بإضافة أعضاء لفريقك من النموذج المجاور.": "Start adding members to your team from the adjacent form.",
    "هل أنت متأكد من حذف هذا العضو؟": "Are you sure you want to remove this member?",
    "اختر دوراً...": "Choose a role...",
    "محرر": "Editor",
    "مقيّم": "Reviewer",
    "صاحب قرار": "Approver",
    "دور الفريق": "Team Role",

    # ─── Pipeline ───
    "خط التوظيف": "Pipeline",
    "تتبع المرشحين": "Candidate Tracking",
    "بحث بالاسم / الإيميل...": "Search by name / email...",
    "ربط مرشح": "Link Candidate",
    "الأنشطة الأخيرة": "Recent Activities",
    "الأنشطة": "Activities",
    "الإجمالي": "Total",
    "لا يوجد مرشحون": "No candidates found",
    "لا توجد نشاطات حتى الآن.": "No activities yet.",
    "لا توجد أنشطة بعد": "No activities yet.",
    "تنقل": "Move",

    # ─── Profile Hints ───
    "أضف صورة شخصية": "Add a profile picture",
    "أضف اسمك الكامل": "Add your full name",
    "أضف رقم هاتفك": "Add your phone number",
    "أضف موقعك الجغرافي": "Add your location",
    "أضف نبذة عنك": "Add a bio",
    "أضف سيرتك الذاتية (CV)": "Add your CV",
    "أضف مهاراتك": "Add your skills",
    "أضف مسمّاك الوظيفي": "Add your job title",
    "تقييم": "Rate",
    "تعليق": "Comment",
    "دعوة مقابلة": "Interview Invite",
    "إرسال إيميل": "Send Email",
    "إضافة للمختارين": "Shortlist",
    "السيرة الذاتية": "CV",
    "نقل إلى:": "Move to:",
    "اختر مرحلة...": "Choose stage...",
    "معلومات": "Info",
    "التقييم": "Rating",
    "التعليقات": "Comments",
    "ملاحظات": "Notes",
    "متوسط تقييم الفريق:": "Average Team Rating:",
    "تقييمك:": "Your Rating:",
    "لم تقيّم بعد": "Not rated yet",
    "اكتب تعليقك هنا...": "Write your comment here...",
    "إرسال": "Send",
    "إرسال بريد إلكتروني": "Send Email",
    "عرض وظيفي": "Job Offer",
    "إشعار رفض": "Rejection Notice",
    "متابعة": "Continue",
    "إلى": "To",
    "الموضوع": "Subject",
    "موضوع الرسالة": "Email Subject",
    "نص الرسالة": "Message Body",
    "اكتب نص الرسالة هنا...": "Write message body here...",
    "مختار": "Shortlisted",
    "تمرير": "Scroll",
    "التالي": "Next",
    "السابق": "Previous",

    # ─── Profile (Removed from ar_translations, moving to en_translations) ───
}

en_translations = {
    # ─── Profile ───
    "My Profile": "ملفي الشخصي",
    "Profile Completion": "اكتمال الملف",
    "Personal Info": "بيانات شخصية",
    "Professional": "بيانات مهنية",
    "Documents": "مستندات",
    "Company Info": "بيانات الشركة",
    "My Role": "دوري",
    "Account Settings": "إعدادات الحساب",
    "Shareable Link": "رابط المشاركة",
    "Copy": "نسخ",
    "Copied!": "تم النسخ!",
    "Personal Information": "البيانات الشخصية",
    "First Name": "الاسم الأول",
    "Last Name": "اسم العائلة",
    "Phone": "رقم الهاتف",
    "Location": "الموقع",
    "Bio — About Me": "نبذة عني",
    "Save Changes": "حفظ التغييرات",
    "Professional Information": "البيانات المهنية",
    "Current Job Title": "المسمى الوظيفي الحالي",
    "Years of Experience": "سنوات الخبرة",
    "Skills": "المهارات",
    "(comma-separated)": "(مفصولة بفاصلة)",
    "About Me / Bio": "نبذة عني",
    "Availability": "التوفر",
    "Immediately / 1 month…": "فوراً / شهر...",
    "Expected Salary": "الراتب المتوقع",
    "e.g. $70K/year": "مثال: 70 ألف دولار/سنوياً",
    "Links & Profiles": "الروابط والحسابات",
    "Current CV": "السيرة الذاتية الحالية",
    "View CV": "عرض السيرة الذاتية",
    "Replace CV": "استبدال السيرة الذاتية",
    "Upload CV": "رفع السيرة الذاتية",
    "max 5MB": "بحد أقصى 5 ميجابايت",
    "Your Links": "روابطك",
    "Company Information": "بيانات الشركة",
    "Company Logo": "شعار الشركة",
    "Upload Logo": "رفع الشعار",
    "Company Name": "اسم الشركة",
    "Industry": "مجال العمل",
    "Company Size": "حجم الشركة",
    "Select…": "اختر...",
    "Website": "الموقع الإلكتروني",
    "Description": "الوصف",
    "Save Company Info": "حفظ بيانات الشركة",
    "Public Company Page": "صفحة الشركة العامة",
    "Share your company page to showcase your brand and open positions.": "شارك صفحة شركتك لعرض وظائفك المتاحة.",
    "View Public Page": "عرض الصفحة العامة",
    "Position / Department": "المنصب / القسم",
    "Change Password": "تغيير كلمة المرور",
    "Current Password": "كلمة المرور الحالية",
    "New Password": "كلمة المرور الجديدة",
    "Confirm New Password": "تأكيد كلمة المرور الجديدة",
    "Update Password": "تحديث كلمة المرور",
    "Danger Zone": "منطقة الخطر",
    "Disabling your account will prevent you from logging in. This action cannot be easily undone.": "تعطيل حسابك سيمنعك من تسجيل الدخول. لا يمكن التراجع عن هذا الإجراء بسهولة.",
    "Delete / Disable Account": "حذف / تعطيل الحساب",
    "Type your username to confirm:": "اكتب اسم المستخدم للتأكيد:",
    "Disable My Account": "تعطيل حسابي"
}

def make_mo_content(translations):
    """Create .mo binary content from a dict of original->translation."""
    sorted_items = sorted(translations.items())
    keys = [k for k, v in sorted_items]
    values = [v for k, v in sorted_items]

    if not keys or keys[0] != "":
        keys.insert(0, "")
        values.insert(0, "Project-Id-Version: 1.0\nContent-Type: text/plain; charset=UTF-8\nContent-Transfer-Encoding: 8bit\n")

    n = len(keys)
    header_size = 28
    key_table_offset = header_size
    val_table_offset = header_size + 8 * n
    strings_offset = header_size + 16 * n

    kdata = b""
    k_offsets = []
    for k in keys:
        enc = k.encode("utf-8")
        k_offsets.append((len(enc), strings_offset + len(kdata)))
        kdata += enc + b"\0"

    vdata = b""
    v_offsets = []
    v_start = strings_offset + len(kdata)
    for v in values:
        enc = v.encode("utf-8")
        v_offsets.append((len(enc), v_start + len(vdata)))
        vdata += enc + b"\0"

    result = struct.pack(
        "<IIIIIII",
        0x950412de, 0, n,
        key_table_offset,
        val_table_offset,
        0, 0
    )

    for length, pos in k_offsets:
        result += struct.pack("<II", length, pos)

    for length, pos in v_offsets:
        result += struct.pack("<II", length, pos)

    result += kdata
    result += vdata
    return result


def write_po(path, translations, lang_code, lang_name):
    lines = [
        f'# {lang_name} translations\n',
        'msgid ""\n',
        'msgstr ""\n',
        '"Content-Type: text/plain; charset=UTF-8\\n"\n',
        '"Content-Transfer-Encoding: 8bit\\n"\n',
        f'"Language: {lang_code}\\n"\n',
        '\n',
    ]
    for orig, trans in translations.items():
        lines.append(f'\nmsgid "{orig}"\n')
        lines.append(f'msgstr "{trans}"\n')
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"  Written: {path}")


ar_po = {}
for k in ar_translations.keys():
    ar_po[k] = k

for k, v in en_translations.items():
    ar_po[k] = v

en_po = ar_translations.copy()
for k in en_translations.keys():
    en_po[k] = k

os.makedirs("locale/ar/LC_MESSAGES", exist_ok=True)
os.makedirs("locale/en/LC_MESSAGES", exist_ok=True)

write_po("locale/ar/LC_MESSAGES/django.po", ar_po, "ar", "Arabic")
write_po("locale/en/LC_MESSAGES/django.po", en_po, "en", "English")

def write_mo(path, translations_dict):
    content = make_mo_content(translations_dict)
    with open(path, "wb") as f:
        f.write(content)
    print(f"  Written MO: {path}")

write_mo("locale/ar/LC_MESSAGES/django.mo", ar_po)
write_mo("locale/en/LC_MESSAGES/django.mo", en_po)

print("Done! Translation files created and compiled.")
