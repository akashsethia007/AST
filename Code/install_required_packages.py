import subprocess
import sys

def install_requirements(requirements_file='requirements.txt'):
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
        print(f"✅ Successfully installed packages from {requirements_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
    except FileNotFoundError:
        print(f"📁 File not found: {requirements_file}")

# Run it
install_requirements('C:\\Users\\User\\PycharmProjects\\AST\\requirements.txt')