.. _ReferenceUsefulXMLSyntax:

Useful XML Syntax
=================

Standard XML placeholders can be used to simplify some scripts.  For example, the following (abbreviated) code ensures that the limits of a domain are symmetric.

.. code-block:: xmds2

    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE simulation [
    <!ENTITY Npts    "64">
    <!ENTITY L      "3.0e-5">
    ]>
      <simulation xmds-version="2">
      
        . . .
        
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
              <dimension name="x" lattice="&Npts;"  domain="(-&L;, &L;)" />
            </transverse_dimensions>
         </geometry>
