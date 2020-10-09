<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="17008000">
	<Property Name="varPersistentID:{1FD84BDE-84CD-4C11-8894-D39918B56A1C}" Type="Ref">/My Computer/Epics_client_virtual_folder/epics_library_client.lvlib/opc_bins</Property>
	<Property Name="varPersistentID:{331C31DF-8C7B-405B-8548-33F0D4E69FF9}" Type="Ref">/My Computer/Epics_client_virtual_folder/epics_library_client.lvlib/opc_2dot5</Property>
	<Property Name="varPersistentID:{405FE393-896B-4FDE-A933-53024A81B54B}" Type="Ref">/My Computer/Epics_client_virtual_folder/epics_library_client.lvlib/opc_humidity</Property>
	<Property Name="varPersistentID:{98C79CD5-4A05-4FAB-810E-7E90F6D782F3}" Type="Ref">/My Computer/Epics_client_virtual_folder/epics_library_client.lvlib/opc_ambient_temp</Property>
	<Property Name="varPersistentID:{A56896DD-E22F-4BC4-92E4-231371252910}" Type="Ref">/My Computer/Epics_client_virtual_folder/epics_library_client.lvlib/opc_pm10</Property>
	<Property Name="varPersistentID:{BBBA5AB5-2D4D-469D-BE57-932EA71B0525}" Type="Ref">/My Computer/Epics_client_virtual_folder/epics_library_client.lvlib/opc_pm1</Property>
	<Property Name="varPersistentID:{C79049D3-B5C9-4C49-A512-E69A971BA393}" Type="Ref">/My Computer/Epics_client_virtual_folder/epics_library_client.lvlib/opc_enable</Property>
	<Property Name="varPersistentID:{F88EB77A-8EAE-404D-91EE-123E5B2A4997}" Type="Ref">/My Computer/Epics_client_virtual_folder/epics_library_client.lvlib/opc_flowrate</Property>
	<Item Name="My Computer" Type="My Computer">
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="Epics_client_virtual_folder" Type="Folder">
			<Item Name="epics_library_client.lvlib" Type="Library" URL="../epics_library_client.lvlib"/>
		</Item>
		<Item Name="Main_UI.vi" Type="VI" URL="../Main_UI.vi"/>
		<Item Name="Numeric_flat.ctl" Type="VI" URL="../Numeric_flat.ctl"/>
		<Item Name="Dependencies" Type="Dependencies"/>
		<Item Name="Build Specifications" Type="Build"/>
	</Item>
</Project>
