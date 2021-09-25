import setuptools

with open('README.md', 'r', encoding='utf-8') as f_desc:
    long_description = f_desc.read()

setuptools.setup(
    name='rubysubs',
    version='0.1.4',
    author='Bent',
    author_email='bent@mail.de',
    description='Tool/library to add ruby text to subtitles',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/RicBent/rubysubs',
    packages=['rubysubs'],
    entry_points={
        'console_scripts': [
            'rubysubs = rubysubs.__main__:main',
        ],
    },
    install_requires=[
        'cchardet',
        'pysubs2',
        'PyQt5'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
    ],
)
