.. _ReferenceSchema:

****************
XMDS2 XML Schema
****************


There are many, many XML tags that can make up an XMDS2 script. Most of them are optional, or have default values if not specified. It is, however, useful to know which elements are possible, and their position and relationship to other elements in the script. Shown below is the full XML tree for XMDS2, which shows all possible elements and their position in the tree. An ellipsis (...) outside an element indicates the element above can be repeated indefinitely, and an ellipsis inside an element (<element> ... </element>) indicates that the structure of that element has already been shown previously.

The syntax <element /> can be used for lowest-level elements that have attributes but no content, and are shorthand for <element> </element>. This shorthand notation can also be used for elements which can only contain the content "yes" or "no"; in this case the presence of <element /> is equivalent to <element> yes </element>, and the absence of such an element is equivalent to <element> no </element>

The possible attributes and attribute values for each element are not shown; see the individual entries in the Reference section for details.


.. parsed-literal::

    <?xml version="1.0" encoding="UTF-8"?>
    <:ref:`simulation <SimulationElement>` xmds-version="2">
      <:ref:`name <NameElement>`> <:ref:`/name <NameElement>`>
      <:ref:`author <AuthorElement>`> <:ref:`author <AuthorElement>`>
      <:ref:`description <DescriptionElement>`> <:ref:`/description <DescriptionElement>`>
      
      <:ref:`testing <TestingElement>`> 
        <:ref:`command_line <CommandLineElement>`> <:ref:`/command_line <CommandLineElement>`>
        <:ref:`arguments <ArgumentsElement>`>
          <:ref:`argument <ArgumentElement>` />
          <:ref:`argument <ArgumentElement>` />
          ...
        <:ref:`/arguments <ArgumentsElement>`>
        <:ref:`input_xsil_file <InputXSILFileElement>` />
        <:ref:`xsil_file <XSILFileElement>`>
          <:ref:`moment_group <MomentGroupElement>` />
          <:ref:`moment_group <MomentGroupElement>` />
          ...
        <:ref:`/xsil_file <XSILFileElement>`>
      <:ref:`/testing <TestingElement>`>
  
      <:ref:`features <FeaturesElement>`>
        <:ref:`arguments <ArgumentsElement>`>
          <:ref:`argument <ArgumentElement>` />
          <:ref:`argument <ArgumentElement>` />
          ...
        <:ref:`/arguments <ArgumentsElement>`>
        <:ref:`auto_vectorise <AutoVectorise>` />
        <:ref:`benchmark <Benchmark>` />
        <:ref:`bing <Bing>` />
        <:ref:`cflags <CFlags>`> <:ref:`/cflags <CFlags>`>
        <:ref:`diagnostics <Diagnostics>` />
        <:ref:`error_check <ErrorCheck>` />
        <:ref:`halt_non_finite <HaltNonFinite>` />
        <:ref:`fftw <FFTW>` />
        <:ref:`globals <Globals>`> <:ref:`/globals <Globals>`>
        <:ref:`openmp <OpenMP>` />
        <:ref:`precision <Precision>`> <:ref:`/precision <Precision>`>
        <:ref:`validation <Validation>` />
      <:ref:`/features <FeaturesElement>`>

      <:ref:`driver <DriverElement>` />
  
      <:ref:`geometry <GeometryElement>`>
        <:ref:`propagation_dimension <PropagationDimensionElement>`> <:ref:`/propagation_dimension <PropagationDimensionElement>`>
        <:ref:`transverse_dimensions <TransverseDimensionsElement>`>
          <:ref:`dimension <DimensionElement>` />
          <:ref:`dimension <DimensionElement>` />
          ...
        <:ref:`/transverse_dimensions <TransverseDimensionsElement>`>
      <:ref:`/geometry <GeometryElement>`>
  
      <:ref:`noise_vector <NoiseVectorElement>`>
        <:ref:`components <ComponentsElement>`> <:ref:`/components <ComponentsElement>`>
      <:ref:`/noise_vector <NoiseVectorElement>`>

      <:ref:`noise_vector <NoiseVectorElement>`> ... <:ref:`/noise_vector <NoiseVectorElement>`>
      <:ref:`noise_vector <NoiseVectorElement>`> ... <:ref:`/noise_vector <NoiseVectorElement>`>
      ...

      <:ref:`vector <VectorElement>`>
        <:ref:`components <ComponentsElement>`> <:ref:`/components <ComponentsElement>`>
        <:ref:`initialisation <InitialisationElement>`>
          <:ref:`dependencies <Dependencies>`> <:ref:`/dependencies <Dependencies>`>
          <:ref:`filename <FilenameElement>`>
          <![:ref:`CDATA <XMDSCSyntax>` [
          ]]>
        <:ref:`/initialisation <InitialisationElement>`>
      <:ref:`/vector <VectorElement>`>

      <:ref:`vector <VectorElement>`> ... <:ref:`/vector <VectorElement>`>
      <:ref:`vector <VectorElement>`> ... <:ref:`/vector <VectorElement>`>
      ...

      <:ref:`computed_vector <ComputedVectorElement>`>
        <:ref:`components <ComponentsElement>`> <:ref:`/components <ComponentsElement>`>
        <:ref:`evaluation <EvaluationElement>`>
          <:ref:`dependencies <Dependencies>`> <:ref:`/dependencies <Dependencies>`>
          <![:ref:`CDATA <XMDSCSyntax>` [
          ]]>
        <:ref:`/evaluation <EvaluationElement>`>
      <:ref:`/computed_vector <ComputedVectorElement>`>

      <:ref:`computed_vector <ComputedVectorElement>`> ... <:ref:`/computed_vector <ComputedVectorElement>`>
      <:ref:`computed_vector <ComputedVectorElement>`> ... <:ref:`/computed_vector <ComputedVectorElement>`>
      ...

      <:ref:`sequence <SequenceElement>`>

        <:ref:`filter <FilterElement>`>
          <:ref:`dependencies <Dependencies>`> <:ref:`/dependencies <Dependencies>`>
          <![:ref:`CDATA <XMDSCSyntax>` [
          ]]>
        <:ref:`/filter <FilterElement>`>

        <:ref:`integrate <IntegrateElement>`>
          <:ref:`samples <SamplesElement>`> <:ref:`/samples <SamplesElement>`>

          <:ref:`computed_vector <ComputedVectorElement>`> ... <:ref:`/computed_vector <ComputedVectorElement>`>

          <:ref:`filters <FiltersElement>`>
            <:ref:`filter <FilterElement>`> ... <:ref:`/filter <FilterElement>`>
            <:ref:`filter <FilterElement>`> ... <:ref:`/filter <FilterElement>`>
            ...
          <:ref:`/filters <FiltersElement>`>
      
          <:ref:`operators <OperatorsElement>`>

            <:ref:`operator <OperatorElement>`>
              <:ref:`boundary_condition <BoundaryConditionElement>`>
                <:ref:`dependencies <Dependencies>`> <:ref:`/dependencies <Dependencies>`>
                <![:ref:`CDATA <XMDSCSyntax>` [
                ]]>
              <:ref:`/boundary_condition <BoundaryConditionElement>`>
              <:ref:`operator_names <OperatorNamesElement>`> <:ref:`/operator_names <OperatorNamesElement>`>
              <:ref:`dependencies <Dependencies>`> <:ref:`/dependencies <Dependencies>`>
              <![:ref:`CDATA <XMDSCSyntax>` [
              ]]>
            <:ref:`/operator <OperatorElement>`>

            <:ref:`operator <OperatorElement>`> ... <:ref:`/operator <OperatorElement>`>
            <:ref:`operator <OperatorElement>`> ... <:ref:`/operator <OperatorElement>`>
            ...

            <:ref:`integration_vectors <IntegrationVectorsElement>`> <:ref:`/integration_vectors <IntegrationVectorsElement>`>
            <:ref:`dependencies <Dependencies>`> <:ref:`/dependencies <Dependencies>`>
            <![:ref:`CDATA <XMDSCSyntax>` [
            ]]>

          <:ref:`/operators <OperatorsElement>`>

        <:ref:`/integrate <IntegrateElement>`>
    
        <:ref:`breakpoint <BreakpointElement>`>
          <:ref:`dependencies <Dependencies>`> <:ref:`/dependencies <Dependencies>`>
        <:ref:`/breakpoint <BreakpointElement>`>

      <:ref:`/sequence <SequenceElement>`>
  
      <:ref:`output <OutputElement>`>
        <:ref:`group <GroupElement>`>
          <:ref:`sampling <SamplingElement>`>
            <:ref:`dependencies <Dependencies>`> <:ref:`/dependencies <Dependencies>`>
            <:ref:`moments <MomentsElement>`> <:ref:`/moments <MomentsElement>`>
            <:ref:`operator <OperatorElement>`> ... <:ref:`/operator <OperatorElement>`>       
            <![:ref:`CDATA <XMDSCSyntax>` [
            ]]>
          <:ref:`/sampling <SamplingElement>`>
        <:ref:`/group <GroupElement>`>

        <:ref:`group <GroupElement>`> ... <:ref:`/group <GroupElement>`>
        <:ref:`group <GroupElement>`> ... <:ref:`/group <GroupElement>`>
        ...

      <:ref:`/output <OutputElement>`>

    <:ref:`/simulation <SimulationElement>`>
