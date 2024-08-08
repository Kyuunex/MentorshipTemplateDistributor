from distutils.core import setup

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
        'discord.py[voice]==2.3.2',
        'psutil',
        'aiosqlite',
        'feedparser',
        'python-dateutil',
        'appdirs',
    ],
)
