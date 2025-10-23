import tibco.tea

# Initialize the TEA object with your server details and admin credentials
tea = tibco.tea.EnterpriseAdministrator(url="http://localhost:8777", user="admin", pwd="admin")

# Create a new user with a password
new_user = tea.users.create(name="new_user", password="secure_password")

# Optional: Assign a role to the new user
# Replace 'MonitorRole' with the actual role you want to assign
roles = tea.roles.find(name='MonitorRole')
if roles:
    new_user.roles.append(roles[0])

print(f"User '{new_user.name}' created with roles: {[role.name for role in new_user.roles]}")
