from setuptools import setup

from mtd.manifest import VERSION

setup(
    name='mtd',
    packages=[
        'mtd',
        'mtd.classes',
        'mtd.cogs',
        'mtd.embeds',
        'mtd.modules',
        'mtd.reusables'
    ],
    version=VERSION,
    description='A Discord bot that automates the Mentorship Discord server speedmapping contest beatmap template distribution.',
    author='Kyuunex',
    author_email='kyuunex@protonmail.ch',
    url='https://github.com/Kyuunex/MTD',
    install_requires=[
        'discord.py==2.5.2',
        'psutil',
        'aiosqlite',
        'python-dateutil',
        'appdirs',
    ],
)
