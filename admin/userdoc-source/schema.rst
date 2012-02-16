.. _Schema:

****************
XMDS2 XML Schema
****************


There are many, many XML tags that can make up an XMDS2 script. Most of them are optional, or have default values if not specified. It is, however, useful to know which elements are possible, and their position and relationship to other elements in the script. Shown below is the full XML tree for XMDS2, which shows all possible elements and their position in the tree. An ellipsis (...) outside an element indicates the element above can be repeated indefinitely, and an ellipsis inside an element (<element> ... </element>) indicates that the structure of that element has already been shown previously.

The possible attributes and attribute values for each element are not shown; see the individual entries in the rest of the Reference section for details.

.. parsed-literal::

    <?xml version="1.0" encoding="UTF-8"?>
    <:ref:`simulation <SimulationElement>` xmds-version="2">
      <name> </name>
      <author> </author>
      <description> </description>

      <testing> </testing>
  
      <:ref:`features <FeaturesElement>`>
        <arguments>
          <argument />
          <argument />
          ...
        </arguments>
        <auto_vectorise />
        <benchmark />
        <bing />
        <cflags> </cflags>
        <diagnostics />
        <:ref:`error_check <ErrorCheck>` />
        <halt_non_finite />
        <fftw />
        <globals> </globals>
        <openmp />
        <:ref:`precision <Precision>`> <:ref:`/precision <Precision>`>
        <validation />
      </features>

      <driver />
  
      <geometry>
        <propagation_dimension> </propagation_dimension>
        <transverse_dimensions>
          <dimension />
          <dimension />
          ...
        </transverse_dimensions>
      </geometry>
  
      <noise_vector>
        <components> </components>
      </noise_vector>

      <noise_vector> ... </noise_vector>
      <noise_vector> ... </noise_vector>
      ...

      <vector>
        <components> </components>
        <initialisation>
          <dependencies> </dependencies>
          <filename />
          <![CDATA[
          ]]>
        </initialisation>
      </vector>

      <vector> ... </vector>
      <vector> ... </vector>
      ...

      <computed_vector>
        <components> </components>
        <evaluation>
          <dependencies> </dependencies>
          <![CDATA[
          ]]>
        </evaluation>
      </computed_vector>

      <computed_vector> ... </computed_vector>
      <computed_vector> ... </computed_vector>
      ...

      <sequence>

        <filter>
          <dependencies> </dependencies>
          <![CDATA[
          ]]>
        </filter>

        <integrate>
          <samples> </samples>

          <computed_vector> ... </computed_vector>

          <filters>
            <filter> ... </filter>
            <filter> ... </filter>
            ...
          </filters>
      
          <operators>

            <operator>
              <boundary_condition>
                <dependencies> </dependencies>
                <![CDATA[
                ]]>
              </boundary_condition>
              <operator_names> </operator_names>
              <dependencies> </dependencies>
              <![CDATA[
              ]]>
            </operator>

            <operator> ... </operator>
            <operator> ... </operator>
            ...

            <integration_vectors> </integration_vectors>
            <dependencies> </dependencies>
            <![CDATA[
            ]]>

          </operators>

        </integrate>
    
        <breakpoint>
          <dependencies> </dependencies>
        </breakpoint>

      </sequence>
  
      <output>
        <group>
          <sampling>  
            <dependencies> </dependencies>
            <moments> </moments>
            <operator> ... </operator>        
            <![CDATA[
            ]]>
          </sampling>
        </group>

        <group> ... </group>
        <group> ... </group>
        ...

      </output>

    </simulation>


