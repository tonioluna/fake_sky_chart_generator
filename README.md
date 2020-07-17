# Fake/Random Sky Chart Generator
I started writting this code mostly for fun but also because I needed some fake sky charts for a web site's background. As such the generated chart needs to fit with iself both vertically and horizontally. That is, when set as a repeating tile background, it will have continous appearence. That is the main reason for charts to be fake, so I can make charts that meet this particular condition. Charts from the actual sky would not have continous boundaries if placed next to themselves.

The development is still WIP as I don't really finish any project every, I keep adding stuff every now and then. However most of the basic functionality is complete. In the future I might add some additional stuff like names for stars or deep space objects or even draw some nebulae. Object identifiers would be fake as well (maybe FGCxxx for Fake General Catalog). The constellation generator with algorithm Delaunay works ok. It can be improved but it works way better than the previous ones.

![Image](../master/doc/chart.delaunay.demo.png?raw=true)

# Installation
The following python modules are required (use pip):
## svgwrite
Required
## scipy
Required only if using the constellation algorithm 'delaunay', which is the default for some charts
## wand
Required only if conversion to PNG is done with the script. The module will require Image Magick to be installed (a descriptive error is shown with instructions if the module is not found). See http://docs.wand-py.org/en/latest/guide/install.html
