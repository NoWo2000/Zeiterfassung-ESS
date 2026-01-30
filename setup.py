from py2exe import freeze

input_version = str(input("Bitte Version angeben (1.0.6): "))

freeze(
    windows=[{
        'script' : 'main.pyw',
        'icon_resources' : [
            (0, 'icon.ico')
        ]
    }],
    zipfile='library.zip',
    version_info={
        'version' : str(input_version + '.0'),
        'product_name' : 'Smart ESS',
        'product_version' : input_version,
        'copyright' : 'Copyright 2023'
    },
    options={
        'packages' : [
            'babel'
        ]
    }
)
