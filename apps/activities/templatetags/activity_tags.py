import re
from django import template
from django.utils.translation import get_language

register = template.Library()

@register.filter(name='translate_activity')
def translate_activity(value):
    """
    Translates known activity log descriptions into Arabic.
    """
    if get_language() != 'ar':
        return value

    val = str(value)

    # 1. User moved candidate to stage
    m = re.match(r"^(.+) moved (.+) to (.+)$", val)
    if m:
        return f"قام {m.group(1)} بنقل {m.group(2)} إلى {m.group(3)}"

    # 2. User shortlisted candidate
    m = re.match(r"^(.+) shortlisted (.+)$", val)
    if m:
        return f"قام {m.group(1)} بإضافة {m.group(2)} للمختارين"

    # 3. User removed shortlist for candidate
    m = re.match(r"^(.+) removed shortlist for (.+)$", val)
    if m:
        return f"قام {m.group(1)} بإزالة {m.group(2)} من المختارين"

    # 4. User commented on candidate: text
    m = re.match(r"^(.+) commented on (.+): (.+)$", val)
    if m:
        return f"قام {m.group(1)} بالتعليق على {m.group(2)}: {m.group(3)}"

    # 5. User rated candidate with score/5
    m = re.match(r"^(.+) rated (.+) with (.+)/5$", val)
    if m:
        return f"قيّم {m.group(1)} {m.group(2)} بـ {m.group(3)}/5"

    # 6. User marked candidate as stage
    m = re.match(r"^(.+) marked (.+) as (.+)$", val)
    if m:
        return f"قام {m.group(1)} بتحديد {m.group(2)} كـ {m.group(3)}"

    # 7. User linked candidate to job
    m = re.match(r"^(.+) linked (.+) to (.+)$", val)
    if m:
        return f"قام {m.group(1)} بربط {m.group(2)} بالوظيفة {m.group(3)}"

    # 8. User created job job
    m = re.match(r"^(.+) created job (.+)$", val)
    if m:
        return f"قام {m.group(1)} بإنشاء وظيفة {m.group(2)}"

    # 9. User edited job job
    m = re.match(r"^(.+) edited job (.+)$", val)
    if m:
        return f"قام {m.group(1)} بتعديل وظيفة {m.group(2)}"

    # 10. User closed job job
    m = re.match(r"^(.+) closed job (.+)$", val)
    if m:
        return f"قام {m.group(1)} بإغلاق وظيفة {m.group(2)}"

    # 11. User reopened job job
    m = re.match(r"^(.+) reopened job (.+)$", val)
    if m:
        return f"قام {m.group(1)} بإعادة فتح وظيفة {m.group(2)}"

    # 12. User created candidate candidate
    m = re.match(r"^(.+) created candidate (.+)$", val)
    if m:
        return f"قام {m.group(1)} بإضافة المرشح {m.group(2)}"

    return val
