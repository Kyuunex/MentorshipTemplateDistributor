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
    description='osu! Mentorship contest bot',
    author='Kyuunex',
    author_email='kyuunex@protonmail.ch',
    url='https://github.com/Kyuunex/MTD',
    install_requires=[
        'discord.py==2.5.2',
        'psutil',
        'aiosqlite',
        'appdirs',
    ],
)
