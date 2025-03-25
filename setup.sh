echo "Generating Django Secret Key..."
echo "==============================="
docker run digitalshoestring/shoestring-django:v0.0.1 python -c "from django.core.management.utils import get_random_secret_key; print(f'SECRET_KEY={get_random_secret_key()}')" > django_secret_key
echo "Complete"
echo "Generating Admin Password"
echo "==============================="
read -p "Enter a default admin password: " password
if [[ -z "$password" ]]; then
   # $var is empty, do what you want
   echo "> No password provided - generating a random one";
   echo "> Please check the file to see what it is!!";
   password=$(mktemp -u XXXXXXXX)
fi

cat <<EOF > default_password
DEFAULT_ADMIN_PASSWORD=$password
# The default password is set the first time the solution runs
# changing the value here will not change the password
# change your password inside each respective site
EOF

echo "Default password saved in the default_password file"
echo "Complete"