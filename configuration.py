"""Contains transformer configuration information
"""

# The version number of the transformer
TRANSFORMER_VERSION = '2.0'

# The transformer description
TRANSFORMER_DESCRIPTION = 'Plant height estimation from LAS point cloud'

# Short name of the transformer
TRANSFORMER_NAME = 'terra.3dscanner.las2height'

# The sensor associated with the transformer
TRANSFORMER_SENSOR = 'scanner3DTop'

# The transformer type (eg: 'rgbmask', 'plotclipper')
TRANSFORMER_TYPE = 'laser3d_canopyheight'

# The name of the author of the extractor
AUTHOR_NAME = 'Chris Schnaufer'

# The email of the author of the extractor
AUTHOR_EMAIL = 'schnaufer@email.arizona.edu'

# Contributors to this transformer
CONTRUBUTORS = ["Max Burnette", "Zongyang Li"]

# Reposity URI of where the source code lives
REPOSITORY = 'https://github.com/AgPipeline/transformer-las2height.git'
