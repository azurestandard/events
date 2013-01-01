try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup(
    name='aquameta-events',
    version='0.1',
    description='A set of bindings to various event systems which applies a uniform interface to each.',
    author='Aquameta',
    author_email='developers@aquameta.com',
    url='https://github.com/aquameta/events',
    long_description=open('README.md', 'r').read(),

    packages=[ 'events',
               'events.engines' ],

    zip_safe=False,
    dependency_links=[ 'http://github.com/abourget/gevent-socketio/tarball/a1e422d2e11f0e6db3ff71bfd691dd1b7f69abe6#egg=gevent_socketio'
                       'https://github.com/downloads/SiteSupport/gevent/gevent-1.0rc2.tar.gz#egg=gevent' ],

    install_requires=[ 'gevent',
                       'gevent_socketio',
                       'gevent_websocket>=0.3.6',
                       'greenlet>=0.4.0',
                       'hiredis>=0.1.1',
                       'lxml>=3.0.1',
                       'psycopg2>=2.4.5',
                       'redis>=2.7.2',
                       'socketIO_client>=0.3',
                       'websocket_client>=0.8.0',
                       'wsgiref>=0.1.2', ],

    classifiers=[ 'Development Status :: 3 - Alpha',
                  'Intended Audience :: Developers',
                  'Operating System :: OS Independent',
                  'Programming Language :: Python',
                  'Topic :: Utilities' ],
)
