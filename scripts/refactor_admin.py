import os
import re

file_path = os.path.join('accounts', 'admin_views.py')
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace is_ordered=True in queries
content = re.sub(r'is_ordered=True', r'payment_status__in=["review", "paid", "failed"]', content)
content = re.sub(r'order__is_ordered=True', r'order__payment_status__in=["review", "paid", "failed"]', content)

# Replace if not order.is_ordered:
content = re.sub(r'if not order\.is_ordered:', r'if order.payment_status == "pending":', content)

# Update status__in lists
content = re.sub(r"status__in=\['New', 'Accepted'\]", r"status__in=['New', 'Processing']", content)
content = re.sub(r"status__in=\['Accepted', 'pendiente', 'asignado'\]", r"status__in=['Processing', 'Assigned']", content)
content = re.sub(r"status__in=\['New', 'Accepted', 'pendiente', 'asignado'\]", r"status__in=['New', 'Processing', 'Assigned']", content)
content = re.sub(r"status__in=\['New', 'Accepted', 'pendiente'\]", r"status__in=['New', 'Processing']", content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated accounts/admin_views.py queries")
