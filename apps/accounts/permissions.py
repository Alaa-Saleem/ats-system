from django.http import HttpResponseForbidden


def is_system_admin(user):
    return user.is_authenticated and (user.role == "admin" or user.is_superuser)


def is_company_owner(user):
    return user.is_authenticated and user.role == "company_owner" and user.is_owner


def is_team_member(user):
    return user.is_authenticated and user.role == "team_member"


def is_company_staff(user):
    return is_system_admin(user) or is_company_owner(user) or is_team_member(user)

def can_manage_jobs(user):
    return is_system_admin(user) or is_company_owner(user)


def can_view_sensitive_candidate_data(user):
    return is_system_admin(user) or is_company_owner(user)

# --- RBAC Matrix ---

def can_move_pipeline_stage(user):
    # Approvers can do anything a company owner can (move stages)
    # Editors can move stages (but view logic will restrict terminal stages)
    return is_system_admin(user) or is_company_owner(user) or (is_team_member(user) and user.team_role in ['editor', 'approver'])

def can_comment_on_candidate(user):
    return is_system_admin(user) or is_company_owner(user) or (is_team_member(user) and user.team_role in ['editor', 'reviewer', 'approver'])

def can_rate_candidate(user):
    return is_system_admin(user) or is_company_owner(user) or (is_team_member(user) and user.team_role in ['editor', 'reviewer', 'approver'])

def can_approve_reject_candidate(user):
    return is_system_admin(user) or is_company_owner(user) or (is_team_member(user) and user.team_role == 'approver')



def forbidden_response():
    return HttpResponseForbidden("You do not have permission to access this resource.")
