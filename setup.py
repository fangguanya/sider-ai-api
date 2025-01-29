import sys,os,shutil,subprocess
import sider_ai_api
from setuptools import setup,Extension

try:os.chdir(os.path.split(__file__)[0])
except:pass

if "sdist" in sys.argv[1:]:
    if not os.path.isfile("README.rst"):
        if shutil.which("pandoc"):
            cmd="pandoc -t rst -o README.rst README.md"
            print("Running pandoc:",cmd,"...")
            result=subprocess.run(cmd.split(' '))
            print("Return code:",result.returncode)
        else:
            print("Requires the pandoc command to generate README.rst",
                  file=sys.stderr)
            sys.exit(1)
    long_desc=open("README.rst",encoding="utf-8").read()
else:
    long_desc=""

setup(
    name='sider-ai-api',
    version=sider_ai_api.__version__,
    description=sider_ai_api.__doc__.splitlines()[0],
    long_description=long_desc,
    author="qfcy",
    author_email="3076711200@qq.com",
    url="https://github.com/qfcy/sider-ai-api",
    py_modules=['sider_ai_api'],
    keywords=["sider.ai","chatgpt","gemini","claude","llama","o1",
        "deepseek","深度求索"
    ],
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Internet :: WWW/HTTP",
    ],
    install_requires=["requests","brotli"],
)
