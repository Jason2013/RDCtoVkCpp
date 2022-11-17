# coding=utf-8

VULKAN_DEVICE_H = """// Copyright (c) 2018-2020,  Zhirnov Andrey. For more information see 'LICENSE'

#pragma once

#include "framework/Window/IWindow.h"

namespace FGC
{{
	static constexpr VkQueueFlagBits	VK_QUEUE_PRESENT_BIT = VkQueueFlagBits(0x80000000u);


	//
	// Vulkan Device
	//

	class VulkanDevice : public VulkanDeviceFn
	{{
	// types
	public:
		struct QueueCreateInfo
		{{
			VkQueueFlags			flags		= 0;
			float					priority	= 0.0f;

			QueueCreateInfo () {{}}
			QueueCreateInfo (int flags, float priority = 0.0f) : flags{{VkQueueFlags(flags)}}, priority{{priority}} {{}}
			QueueCreateInfo (VkQueueFlags flags, float priority = 0.0f) : flags{{flags}}, priority{{priority}} {{}}
		}};

		struct VulkanQueue
		{{
			VkQueue					handle		= VK_NULL_HANDLE;
			uint					familyIndex	= UMax;
			uint					queueIndex	= UMax;
			VkQueueFlags			flags		= 0;
			float					priority	= 0.0f;
		}};

		static constexpr uint	maxQueues = 32;

		using SurfaceCtor_t = std::function< VkSurfaceKHR (VkInstance) >;
		using Queues_t		= FixedArray< VulkanQueue, maxQueues >;


	// variables
	private:
		VkDevice					_vkDevice;
		Queues_t					_vkQueues;

		VkSurfaceKHR				_vkSurface;
		VkPhysicalDevice			_vkPhysicalDevice;
		VkInstance					_vkInstance;
		uint                        _apiVersion = 0;
		bool						_usedSharedInstance;

		VulkanDeviceFnTable			_deviceFnTable;

		// enabled features
		struct {{
			VkPhysicalDeviceFeatures main;
			VkPhysicalDeviceVulkan11Features vulkan11;
			VkPhysicalDeviceVulkan12Features vulkan12;
			VkPhysicalDeviceVulkan13Features vulkan13;
{FEATURE_DECLARATIONS}
		}}	_features;


	// methods
	public:
		VulkanDevice ();
		~VulkanDevice ();
		
		bool Create (UniquePtr<IVulkanSurface>	surf,
					 NtStringView				applicationName,
					 NtStringView				engineName,
					 uint						version				= VK_API_VERSION_1_1,
					 StringView					deviceName			= Default,
					 ArrayView<QueueCreateInfo>	queues				= Default,
					 ArrayView<const char*>		instanceLayers		= GetRecomendedInstanceLayers(),
					 ArrayView<const char*>		instanceExtensions	= GetRecomendedInstanceExtensions(),
					 ArrayView<const char*>		deviceExtensions	= GetRecomendedDeviceExtensions());
		
		bool Create (NtStringView				applicationName,
					 NtStringView				engineName,
					 uint						version				= VK_API_VERSION_1_1,
					 StringView					deviceName			= Default,
					 ArrayView<QueueCreateInfo>	queues				= Default,
					 ArrayView<const char*>		instanceLayers		= GetRecomendedInstanceLayers(),
					 ArrayView<const char*>		instanceExtensions	= GetRecomendedInstanceExtensions(),
					 ArrayView<const char*>		deviceExtensions	= GetRecomendedDeviceExtensions());

		bool Create (VkInstance					instance,
					 UniquePtr<IVulkanSurface>	surf,
					 StringView					deviceName			= Default,
					 ArrayView<QueueCreateInfo>	queues				= Default,
					 ArrayView<const char*>		deviceExtensions	= GetRecomendedDeviceExtensions());

		void Destroy ();
		
		ND_ VkInstance					GetVkInstance ()			const	{{ return _vkInstance; }}
		ND_ VkPhysicalDevice			GetVkPhysicalDevice ()		const	{{ return _vkPhysicalDevice; }}
		ND_ VkDevice					GetVkDevice ()				const	{{ return _vkDevice; }}
		ND_ VkSurfaceKHR				GetVkSurface ()				const	{{ return _vkSurface; }}
		ND_ ArrayView<VulkanQueue>		GetVkQueues ()				const	{{ return _vkQueues; }}

		ND_ VkPhysicalDeviceFeatures const&								GetDeviceFeatures ()							const	{{ return _features.main; }}
{FUNCTION_DEFINITIONS}

		ND_ static ArrayView<const char*>	GetRecomendedInstanceLayers ();
		ND_ static ArrayView<const char*>	GetRecomendedInstanceExtensions ();
		ND_ static ArrayView<const char*>	GetRecomendedDeviceExtensions ();
		ND_ static ArrayView<const char*>	GetAllDeviceExtensions_v100 ();
		ND_ static ArrayView<const char*>	GetAllDeviceExtensions ();


	protected:
		virtual void _OnInstanceCreated (Array<const char*> &&, Array<const char*> &&) {{}}
		virtual void _OnLogicalDeviceCreated (Array<const char *> &&) {{}}
		virtual void _BeforeDestroy () {{}}
		virtual void _AfterDestroy () {{}}
		
		ND_ static StringView  _GetVendorNameByID (uint id);


	private:
		bool _CreateInstance (NtStringView appName, NtStringView engineName, ArrayView<const char*> instanceLayers, Array<const char*> &&instanceExtensions, uint version);
		bool _ChooseGpuDevice (StringView deviceName);
		bool _SetupQueues (ArrayView<QueueCreateInfo> queue);
		bool _CreateDevice (ArrayView<const char*> extensions);
		bool _SetupDeviceFeatures (void** next, ArrayView<const char*> extensions);
		bool _ChooseQueueIndex (ArrayView<VkQueueFamilyProperties> props, INOUT VkQueueFlags &flags, OUT uint &index) const;
		void _DestroyDevice ();

		void _ValidateInstanceVersion (INOUT uint &version) const;
		void _ValidateInstanceLayers (INOUT Array<const char*> &layers) const;
		void _ValidateInstanceExtensions (INOUT Array<const char*> &ext) const;
		void _ValidateDeviceExtensions (INOUT Array<const char*> &ext) const;
	}};


}}	// FGC
"""

VULKAN_DEVICE_CPP = """// Copyright (c) 2018-2020,  Zhirnov Andrey. For more information see 'LICENSE'

#include "VulkanDevice.h"
#include "stl/Containers/StaticString.h"
#include "stl/Algorithms/StringUtils.h"
#include "stl/Algorithms/EnumUtils.h"
#include "stl/Algorithms/Cast.h"
#include <bitset>

namespace FGC
{{

/*
=================================================
	constructor
=================================================
*/
	VulkanDevice::VulkanDevice () :
		_vkDevice{{ VK_NULL_HANDLE }},
		_vkSurface{{ VK_NULL_HANDLE }},
		_vkPhysicalDevice{{ VK_NULL_HANDLE }},
		_vkInstance{{ VK_NULL_HANDLE }},
		_usedSharedInstance{{ false }}
	{{
		VulkanDeviceFn_Init( &_deviceFnTable );
		memset( &_features, 0, sizeof(_features) );
	}}
	
/*
=================================================
	destructor
=================================================
*/
	VulkanDevice::~VulkanDevice ()
	{{
		Destroy();
	}}
	
/*
=================================================
	GetRecomendedInstanceLayers
=================================================
*/
	ArrayView<const char*>  VulkanDevice::GetRecomendedInstanceLayers ()
	{{
		#ifdef PLATFORM_ANDROID
			static const char*	instance_layers[] = {{
				"VK_LAYER_GOOGLE_threading",
				"VK_LAYER_LUNARG_parameter_validation",
				"VK_LAYER_LUNARG_object_tracker",
				"VK_LAYER_LUNARG_core_validation",
				"VK_LAYER_GOOGLE_unique_objects",

				// may be unsupported:
				"VK_LAYER_LUNARG_vktrace",
				"VK_LAYER_ARM_MGD",
				"VK_LAYER_ARM_mali_perf_doc"
			}};
		#else
			static const char*	instance_layers[] = {{
				"VK_LAYER_LUNARG_standard_validation",
				"VK_LAYER_LUNARG_assistant_layer",
				//"VK_LAYER_GOOGLE_threading",					// inside VK_LAYER_LUNARG_standard_validation
				//"VK_LAYER_LUNARG_parameter_validation",		// inside VK_LAYER_LUNARG_standard_validation
				//"VK_LAYER_LUNARG_device_limits",				// inside VK_LAYER_LUNARG_standard_validation
				//"VK_LAYER_LUNARG_object_tracker",				// inside VK_LAYER_LUNARG_standard_validation
				//"VK_LAYER_LUNARG_image",						// inside VK_LAYER_LUNARG_standard_validation
				//"VK_LAYER_LUNARG_core_validation",			// inside VK_LAYER_LUNARG_standard_validation
				//"VK_LAYER_LUNARG_swapchain",					// inside VK_LAYER_LUNARG_standard_validation
				//"VK_LAYER_GOOGLE_unique_objects",				// inside VK_LAYER_LUNARG_standard_validation
				//"VK_LAYER_LUNARG_device_simulation",
				//"VK_LAYER_LUNARG_api_dump",
				//"VK_LAYER_LUNARG_vktrace"
			}};
		#endif
		return instance_layers;
	}}
	
/*
=================================================
	GetRecomendedInstanceExtensions
=================================================
*/
	ArrayView<const char*>  VulkanDevice::GetRecomendedInstanceExtensions ()
	{{
		static const char*	instance_extensions[] =
		{{
			#ifdef VK_KHR_surface
				VK_KHR_SURFACE_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_get_physical_device_properties2
				VK_KHR_GET_PHYSICAL_DEVICE_PROPERTIES_2_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_get_surface_capabilities2
				VK_KHR_GET_SURFACE_CAPABILITIES_2_EXTENSION_NAME,
			#endif
			#ifdef VK_EXT_debug_utils
				VK_EXT_DEBUG_UTILS_EXTENSION_NAME,
			#elif defined VK_EXT_debug_report
				VK_EXT_DEBUG_REPORT_EXTENSION_NAME,
			#endif
		}};
		return instance_extensions;
	}}

/*
=================================================
	GetRecomendedDeviceExtensions
=================================================
*/
	ArrayView<const char*>  VulkanDevice::GetRecomendedDeviceExtensions ()
	{{
		static const char *	device_extensions[] = {{
			"none"
		}};
		return device_extensions;
	}}

/*
=================================================
	GetAllDeviceExtensions_v100
=================================================
*/
	ArrayView<const char*>  VulkanDevice::GetAllDeviceExtensions_v100 ()
	{{
		static const char *	device_extensions[] =
		{{
			#ifdef VK_KHR_get_memory_requirements2
				VK_KHR_GET_MEMORY_REQUIREMENTS_2_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_bind_memory2
				VK_KHR_BIND_MEMORY_2_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_dedicated_allocation
				VK_KHR_DEDICATED_ALLOCATION_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_create_renderpass2
				VK_KHR_CREATE_RENDERPASS_2_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_sampler_ycbcr_conversion
				VK_KHR_SAMPLER_YCBCR_CONVERSION_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_descriptor_update_template
				VK_KHR_DESCRIPTOR_UPDATE_TEMPLATE_EXTENSION_NAME,
			#endif
		}};
		return device_extensions;
	}}

/*
=================================================
	GetAllDeviceExtensions
=================================================
*/
	ArrayView<const char*>  VulkanDevice::GetAllDeviceExtensions ()
	{{
		static const char *	device_extensions[] =
		{{
			#ifdef VK_KHR_create_renderpass2
				VK_KHR_CREATE_RENDERPASS_2_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_draw_indirect_count
				VK_KHR_DRAW_INDIRECT_COUNT_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_8bit_storage
				VK_KHR_8BIT_STORAGE_EXTENSION_NAME,
			#endif
			#ifdef VK_EXT_conservative_rasterization
				VK_EXT_CONSERVATIVE_RASTERIZATION_EXTENSION_NAME,
			#endif
			#ifdef VK_EXT_sample_locations
				VK_EXT_SAMPLE_LOCATIONS_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_push_descriptor
				VK_KHR_PUSH_DESCRIPTOR_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_shader_atomic_int64
				VK_KHR_SHADER_ATOMIC_INT64_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_shader_float16_int8
				VK_KHR_SHADER_FLOAT16_INT8_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_shader_float_controls
				VK_KHR_SHADER_FLOAT_CONTROLS_EXTENSION_NAME,
			#endif
			#ifdef VK_EXT_blend_operation_advanced
				VK_EXT_BLEND_OPERATION_ADVANCED_EXTENSION_NAME,
			#endif
			#ifdef VK_EXT_conditional_rendering
				VK_EXT_CONDITIONAL_RENDERING_EXTENSION_NAME,
			#endif
			#ifdef VK_EXT_inline_uniform_block
				VK_EXT_INLINE_UNIFORM_BLOCK_EXTENSION_NAME,
			#endif
			#ifdef VK_EXT_descriptor_indexing
				VK_EXT_DESCRIPTOR_INDEXING_EXTENSION_NAME,
			#endif
			#ifdef VK_EXT_memory_budget
				VK_EXT_MEMORY_BUDGET_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_shader_clock
				VK_KHR_SHADER_CLOCK_EXTENSION_NAME,
			#endif
			#ifdef VK_KHR_timeline_semaphore
				VK_KHR_TIMELINE_SEMAPHORE_EXTENSION_NAME,
			#endif

			// Vendor specific extensions
			#ifdef VK_NV_mesh_shader
				VK_NV_MESH_SHADER_EXTENSION_NAME,
			#endif
			#ifdef VK_NV_shader_image_footprint
				VK_NV_SHADER_IMAGE_FOOTPRINT_EXTENSION_NAME,
			#endif
			#ifdef VK_NV_shading_rate_image
				VK_NV_SHADING_RATE_IMAGE_EXTENSION_NAME,
			#endif
			#ifdef VK_NV_fragment_shader_barycentric
				VK_NV_FRAGMENT_SHADER_BARYCENTRIC_EXTENSION_NAME,
			#endif
			#ifdef VK_NV_ray_tracing
				VK_NV_RAY_TRACING_EXTENSION_NAME,
			#endif
			#ifdef VK_NVX_device_generated_commands
				VK_NVX_DEVICE_GENERATED_COMMANDS_EXTENSION_NAME,
			#endif
		}};
		return device_extensions;
	}}

/*
=================================================
	Create
=================================================
*/
	bool VulkanDevice::Create (UniquePtr<IVulkanSurface>	surface,
							   NtStringView					appName,
							   NtStringView					engineName,
							   const uint					version,
							   StringView					deviceName,
							   ArrayView<QueueCreateInfo>	queues,
							   ArrayView<const char*>		instanceLayers,
							   ArrayView<const char*>		instanceExtensions,
							   ArrayView<const char*>		deviceExtensions)
	{{
		CHECK_ERR( surface );

		Array<const char*>	inst_ext {{ surface->GetRequiredExtensions() }};
		inst_ext.insert( inst_ext.end(), instanceExtensions.begin(), instanceExtensions.end() );

		CHECK_ERR( _CreateInstance( appName, engineName, instanceLayers, std::move(inst_ext), version ));
		CHECK_ERR( _ChooseGpuDevice( deviceName ));

		_vkSurface = surface->Create( _vkInstance );
		CHECK_ERR( _vkSurface );
		
		CHECK_ERR( _SetupQueues( queues ));
		CHECK_ERR( _CreateDevice( deviceExtensions ));

		return true;
	}}
	
/*
=================================================
	Create
=================================================
*/
	bool VulkanDevice::Create (NtStringView					appName,
							   NtStringView					engineName,
							   const uint					version,
							   StringView					deviceName,
							   ArrayView<QueueCreateInfo>	queues,
							   ArrayView<const char*>		instanceLayers,
							   ArrayView<const char*>		instanceExtensions,
							   ArrayView<const char*>		deviceExtensions)
	{{
		CHECK_ERR( _CreateInstance( appName, engineName, instanceLayers, Array<const char*>{{instanceExtensions}}, version ));
		CHECK_ERR( _ChooseGpuDevice( deviceName ));
		
		CHECK_ERR( _SetupQueues( queues ));
		CHECK_ERR( _CreateDevice( deviceExtensions ));

		return true;
	}}
	
/*
=================================================
	Create
=================================================
*/
	bool VulkanDevice::Create (VkInstance					instance,
							   UniquePtr<IVulkanSurface>	surface,
							   StringView					deviceName,
							   ArrayView<QueueCreateInfo>	queues,
							   ArrayView<const char*>		deviceExtensions)
	{{
		CHECK_ERR( instance );

		_usedSharedInstance	= true;
		_vkInstance			= instance;
		
		CHECK_ERR( VulkanLoader::Initialize() );
		VulkanLoader::LoadInstance( _vkInstance );

		CHECK_ERR( _ChooseGpuDevice( deviceName ));

		if ( surface ) {{
			_vkSurface = surface->Create( _vkInstance );
			CHECK_ERR( _vkSurface );
		}}

		CHECK_ERR( _SetupQueues( queues ));
		CHECK_ERR( _CreateDevice( deviceExtensions ));
		
		return true;
	}}

/*
=================================================
	Destroy
=================================================
*/
	void VulkanDevice::Destroy ()
	{{
		_DestroyDevice();
	}}

/*
=================================================
	_CreateInstance
=================================================
*/
	bool VulkanDevice::_CreateInstance (NtStringView appName, NtStringView engineName,
										ArrayView<const char*> layers, Array<const char*> &&extensions, uint version)
	{{
		CHECK_ERR( not _vkInstance );
		CHECK_ERR( VulkanLoader::Initialize() );
		
		Array< const char* >	instance_layers;
		instance_layers.assign( layers.begin(), layers.end() );

		_ValidateInstanceVersion( INOUT version );
		_ValidateInstanceLayers( INOUT instance_layers );
		_ValidateInstanceExtensions( INOUT extensions );


		VkApplicationInfo		app_info = {{}};
		app_info.sType				= VK_STRUCTURE_TYPE_APPLICATION_INFO;
		app_info.apiVersion			= version;
		app_info.pApplicationName	= appName.c_str();
		app_info.applicationVersion	= 0;
		app_info.pEngineName		= engineName.c_str();
		app_info.engineVersion		= 0;
		
		VkInstanceCreateInfo			instance_create_info = {{}};
		instance_create_info.sType						= VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
		instance_create_info.pApplicationInfo			= &app_info;
		instance_create_info.enabledExtensionCount		= uint(extensions.size());
		instance_create_info.ppEnabledExtensionNames	= extensions.data();
		instance_create_info.enabledLayerCount			= uint(instance_layers.size());
		instance_create_info.ppEnabledLayerNames		= instance_layers.data();

		_apiVersion = version;

		VK_CHECK( vkCreateInstance( &instance_create_info, null, OUT &_vkInstance ));

		VulkanLoader::LoadInstance( _vkInstance );

		_OnInstanceCreated( std::move(instance_layers), std::move(extensions) );
		return true;
	}}
	
/*
=================================================
	_ValidateInstanceVersion
=================================================
*/
	void VulkanDevice::_ValidateInstanceVersion (INOUT uint &version) const
	{{
		const uint	min_ver		= VK_API_VERSION_1_0;
		uint		current_ver	= 0;

		VK_CALL( vkEnumerateInstanceVersion( OUT &current_ver ));

		version = Min( version, Max( min_ver, current_ver ));
	}}

/*
=================================================
	_ValidateInstanceLayers
=================================================
*/
	void VulkanDevice::_ValidateInstanceLayers (INOUT Array<const char*> &layers) const
	{{
		Array<VkLayerProperties> inst_layers;

		// load supported layers
		uint	count = 0;
		VK_CALL( vkEnumerateInstanceLayerProperties( OUT &count, null ));

		if (count == 0)
		{{
			layers.clear();
			return;
		}}

		inst_layers.resize( count );
		VK_CALL( vkEnumerateInstanceLayerProperties( OUT &count, OUT inst_layers.data() ));


		// validate
		for (auto iter = layers.begin(); iter != layers.end();)
		{{
			bool	found = false;

			for (auto& prop : inst_layers)
			{{
				if ( StringView(*iter) == prop.layerName ) {{
					found = true;
					break;
				}}
			}}

			if ( not found )
			{{
				FG_LOGI( "Vulkan layer \\""s << (*iter) << "\\" not supported and will be removed" );

				iter = layers.erase( iter );
			}}
			else
				++iter;
		}}
	}}

/*
=================================================
	_ValidateInstanceExtensions
=================================================
*/
	void VulkanDevice::_ValidateInstanceExtensions (INOUT Array<const char*> &extensions) const
	{{
		using ExtName_t = StaticString<VK_MAX_EXTENSION_NAME_SIZE>;

		HashSet<ExtName_t>	instance_extensions;


		// load supported extensions
		uint	count = 0;
		VK_CALL( vkEnumerateInstanceExtensionProperties( null, OUT &count, null ));

		if ( count == 0 )
		{{
			extensions.clear();
			return;
		}}

		Array< VkExtensionProperties >		inst_ext;
		inst_ext.resize( count );

		VK_CALL( vkEnumerateInstanceExtensionProperties( null, OUT &count, OUT inst_ext.data() ));

		for (auto& ext : inst_ext) {{
			instance_extensions.insert( StringView(ext.extensionName) );
		}}


		// validate
		for (auto iter = extensions.begin(); iter != extensions.end();)
		{{
			if ( instance_extensions.find( ExtName_t{{*iter}} ) == instance_extensions.end() )
			{{
				FG_LOGI( "Vulkan instance extension \\""s << (*iter) << "\\" not supported and will be removed" );

				iter = extensions.erase( iter );
			}}
			else
				 ++iter;
		}}
	}}
	
/*
=================================================
	_ValidateDeviceExtensions
=================================================
*/
	void VulkanDevice::_ValidateDeviceExtensions (INOUT Array<const char*> &extensions) const
	{{
		// load supported device extensions
		uint	count = 0;
		VK_CALL( vkEnumerateDeviceExtensionProperties( _vkPhysicalDevice, null, OUT &count, null ));

		if ( count == 0 )
		{{
			extensions.clear();
			return;
		}}

		Array< VkExtensionProperties >	dev_ext;
		dev_ext.resize( count );

		VK_CALL( vkEnumerateDeviceExtensionProperties( _vkPhysicalDevice, null, OUT &count, OUT dev_ext.data() ));


		// validate
		for (auto iter = extensions.begin(); iter != extensions.end();)
		{{
			bool	found = false;

			for (auto& ext : dev_ext)
			{{
				if ( StringView(*iter) == ext.extensionName )
				{{
					found = true;
					break;
				}}
			}}

			if ( not found )
			{{
				FG_LOGI( "Vulkan device extension \\""s << (*iter) << "\\" not supported and will be removed" );

				iter = extensions.erase( iter );
			}}
			else
				++iter;
		}}
	}}

/*
=================================================
	_GetVendorNameByID
----
	from https://www.reddit.com/r/vulkan/comments/4ta9nj/is_there_a_comprehensive_list_of_the_names_and/
=================================================
*/
	StringView  VulkanDevice::_GetVendorNameByID (uint id)
	{{
		switch ( id )
		{{
			case 0x1002 :	return "AMD";
			case 0x1010 :	return "ImgTec";
			case 0x10DE :	return "NVIDIA";
			case 0x13B5 :	return "ARM";
			case 0x5143 :	return "Qualcomm";
			case 0x8086 :	return "INTEL";
		}}
		return "unknown";
	}}
	
/*
=================================================
	_ChooseGpuDevice
=================================================
*/
	bool VulkanDevice::_ChooseGpuDevice (StringView deviceName)
	{{
		CHECK_ERR( _vkInstance );
		CHECK_ERR( not _vkPhysicalDevice );
		
		uint						count	= 0;
		Array< VkPhysicalDevice >	devices;
		
		VK_CALL( vkEnumeratePhysicalDevices( _vkInstance, OUT &count, null ));
		CHECK_ERR( count > 0 );

		devices.resize( count );
		VK_CALL( vkEnumeratePhysicalDevices( _vkInstance, OUT &count, OUT devices.data() ));
		
		VkPhysicalDevice	match_name_device	= VK_NULL_HANDLE;
		VkPhysicalDevice	high_perf_device	= VK_NULL_HANDLE;
		float				max_performance		= 0.0f;

		for (auto& dev : devices)
		{{
			VkPhysicalDeviceProperties			prop	 = {{}};
			VkPhysicalDeviceFeatures			feat	 = {{}};
			VkPhysicalDeviceMemoryProperties	mem_prop = {{}};
			
			vkGetPhysicalDeviceProperties( dev, OUT &prop );
			vkGetPhysicalDeviceFeatures( dev, OUT &feat );
			vkGetPhysicalDeviceMemoryProperties( dev, OUT &mem_prop );

			FG_LOGI( "Found Vulkan device: "s << prop.deviceName );

			const bool	is_gpu		  = (prop.deviceType == VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU or
										 prop.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU);
			const bool	is_integrated = prop.deviceType == VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU;

			if ( not is_gpu )
				continue;

																									// magic function:
			const float		perf	= //float(info.globalMemory.Mb()) / 1024.0f +							// commented because of bug on Intel (incorrect heap size)
										float(prop.limits.maxComputeSharedMemorySize >> 10) / 64.0f +		// big local cache is good
										float(is_gpu and not is_integrated ? 4 : 1) +						// 
										float(prop.limits.maxComputeWorkGroupInvocations) / 1024.0f +		// 
										float(feat.tessellationShader + feat.geometryShader);

			const bool		nmatch	=	not deviceName.empty()							and
										(HasSubStringIC( prop.deviceName, deviceName )	or
										 HasSubStringIC( _GetVendorNameByID( prop.vendorID ), deviceName ));

			if ( perf > max_performance ) {{
				max_performance		= perf;
				high_perf_device	= dev;
			}}

			if ( nmatch and not match_name_device ) {{
				match_name_device	= dev;
			}}
		}}
			
		_vkPhysicalDevice = (match_name_device ? match_name_device : high_perf_device);
		CHECK_ERR( _vkPhysicalDevice );

		return true;
	}}

/*
=================================================
	_SetupQueues
=================================================
*/
	bool VulkanDevice::_SetupQueues (ArrayView<QueueCreateInfo> queues)
	{{
		CHECK_ERR( _vkQueues.empty() );
		
		constexpr uint	MaxQueueFamilies = 32;
		using QueueFamilyProperties_t	= FixedArray< VkQueueFamilyProperties, MaxQueueFamilies >;
		using QueueCount_t				= FixedArray< uint, MaxQueueFamilies >;

		uint	count = 0;
		vkGetPhysicalDeviceQueueFamilyProperties( _vkPhysicalDevice, OUT &count, null );
		CHECK_ERR( count > 0 );
		
		QueueFamilyProperties_t  queue_family_props;
		queue_family_props.resize( Min( count, queue_family_props.capacity() ));
		vkGetPhysicalDeviceQueueFamilyProperties( _vkPhysicalDevice, OUT &count, OUT queue_family_props.data() );


		// setup default queue
		if ( queues.empty() )
		{{
			uint			family_index	= 0;
			VkQueueFlags	flags			= VkQueueFlags(VK_QUEUE_GRAPHICS_BIT | VK_QUEUE_COMPUTE_BIT);
			
			if ( _vkSurface )
				flags |= VK_QUEUE_PRESENT_BIT;

			CHECK_ERR( _ChooseQueueIndex( queue_family_props, INOUT flags, OUT family_index ));

			_vkQueues.push_back({{ VK_NULL_HANDLE, family_index, UMax, flags, 0.0f }});
			return true;
		}}

		QueueCount_t	qcount;	qcount.resize( queue_family_props.size() );

		for (auto& q : queues)
		{{
			uint			family_index	= 0;
			VkQueueFlags	flags			= q.flags;
			CHECK_ERR( _ChooseQueueIndex( queue_family_props, INOUT flags, OUT family_index ));

			if ( qcount[family_index]++ < queue_family_props[family_index].queueCount )
			{{
				_vkQueues.push_back({{ VK_NULL_HANDLE, family_index, UMax, flags, q.priority }});
			}}
		}}

		return true;
	}}
	
/*
=================================================
	_CreateDevice
=================================================
*/
	bool VulkanDevice::_CreateDevice (ArrayView<const char*> extensions)
	{{
		CHECK_ERR( _vkPhysicalDevice );
		CHECK_ERR( not _vkDevice );
		CHECK_ERR( not _vkQueues.empty() );

		// setup device create info
		VkDeviceCreateInfo		device_info	= {{}};
		void **					next_ext	= const_cast<void **>( &device_info.pNext );
		device_info.sType		= VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;


		// setup extensions
		Array<const char *>		device_extensions;
		device_extensions.assign( extensions.begin(), extensions.end() );

		if ( _vkSurface )
			device_extensions.push_back( VK_KHR_SWAPCHAIN_EXTENSION_NAME );

		_ValidateDeviceExtensions( INOUT device_extensions );

		if ( not device_extensions.empty() )
		{{
			device_info.enabledExtensionCount	= uint(device_extensions.size());
			device_info.ppEnabledExtensionNames	= device_extensions.data();
		}}


		// setup queues
		Array< VkDeviceQueueCreateInfo >	queue_infos;
		Array< FixedArray<float,16> >		priorities;
		{{
			uint	max_queue_families = 0;
			vkGetPhysicalDeviceQueueFamilyProperties( _vkPhysicalDevice, OUT &max_queue_families, null );

			queue_infos.resize( max_queue_families );
			priorities.resize( max_queue_families );

			for (size_t i = 0; i < queue_infos.size(); ++i)
			{{
				auto&	ci = queue_infos[i];

				ci.sType			= VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
				ci.pNext			= null;
				ci.queueFamilyIndex	= uint(i);
				ci.queueCount		= 0;
				ci.pQueuePriorities	= priorities[i].data();
			}}

			for (auto& q : _vkQueues)
			{{
				q.queueIndex = (queue_infos[ q.familyIndex ].queueCount++);
				priorities[ q.familyIndex ].push_back( q.priority );
			}}

			// remove unused queues
			for (auto iter = queue_infos.begin(); iter != queue_infos.end();)
			{{
				if ( iter->queueCount == 0 )
					iter = queue_infos.erase( iter );
				else
					++iter;
			}}
		}}
		device_info.queueCreateInfoCount	= uint(queue_infos.size());
		device_info.pQueueCreateInfos		= queue_infos.data();


		// setup features
		vkGetPhysicalDeviceFeatures( _vkPhysicalDevice, OUT &_features.main );
		device_info.pEnabledFeatures = &_features.main;

		CHECK_ERR( _SetupDeviceFeatures( next_ext, device_extensions ));

		VK_CHECK( vkCreateDevice( _vkPhysicalDevice, &device_info, null, OUT &_vkDevice ));
		

		VulkanLoader::LoadDevice( _vkDevice, OUT _deviceFnTable );

		for (auto& q : _vkQueues) {{
			vkGetDeviceQueue( _vkDevice, q.familyIndex, q.queueIndex, OUT &q.handle );
		}}

		_OnLogicalDeviceCreated( std::move(device_extensions) );
		return true;
	}}
	
/*
=================================================
	_SetupDeviceFeatures
=================================================
*/
	bool VulkanDevice::_SetupDeviceFeatures (void** nextExt, ArrayView<const char*> extensions)
	{{
		VkPhysicalDeviceFeatures2	feat2		= {{}};
		void **						next_feat	= &feat2.pNext;;
		feat2.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2;

		CHECK_ERR( not _apiVersion == 0 );

		uint minorVersion = VK_API_VERSION_MINOR(_apiVersion);
        CHECK_ERR(1 <= minorVersion && minorVersion <= 3);

        if (minorVersion >= VK_API_VERSION_MINOR(VK_API_VERSION_1_1))
        {{
            *next_feat = *nextExt = &_features.vulkan11;
            next_feat = nextExt = &_features.vulkan11.pNext;
            _features.vulkan11.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_FEATURES;
        }}
		if (minorVersion >= VK_API_VERSION_MINOR(VK_API_VERSION_1_2))
        {{
            *next_feat = *nextExt = &_features.vulkan12;
            next_feat = nextExt = &_features.vulkan12.pNext;
            _features.vulkan12.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES;
        }}
		if (minorVersion >= VK_API_VERSION_MINOR(VK_API_VERSION_1_3))
        {{
            *next_feat = *nextExt = &_features.vulkan13;
            next_feat = nextExt = &_features.vulkan13.pNext;
            _features.vulkan13.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES;
        }}
		
		for (StringView ext : extensions)
		{{
			{USE_EXTENSIONS}
		}}

		vkGetPhysicalDeviceFeatures2( GetVkPhysicalDevice(), &feat2 );
		return true;
	}}

/*
=================================================
	_ChooseQueueIndex
=================================================
*/
	bool VulkanDevice::_ChooseQueueIndex (ArrayView<VkQueueFamilyProperties> queueFamilyProps, INOUT VkQueueFlags &requiredFlags, OUT uint &familyIndex) const
	{{
		// validate required flags
		{{
			// if the capabilities of a queue family include VK_QUEUE_GRAPHICS_BIT or VK_QUEUE_COMPUTE_BIT,
			// then reporting the VK_QUEUE_TRANSFER_BIT capability separately for that queue family is optional.
			if ( requiredFlags & (VK_QUEUE_GRAPHICS_BIT | VK_QUEUE_COMPUTE_BIT) )
				requiredFlags &= ~VK_QUEUE_TRANSFER_BIT;
		}}

		Pair<VkQueueFlags, uint>	compatible {{0, UMax}};

		for (size_t i = 0; i < queueFamilyProps.size(); ++i)
		{{
			VkBool32		supports_present = false;
			const auto&		prop			 = queueFamilyProps[i];
			VkQueueFlags	curr_flags		 = prop.queueFlags;
			
			if ( _vkSurface )
			{{
				VK_CALL( vkGetPhysicalDeviceSurfaceSupportKHR( _vkPhysicalDevice, uint(i), _vkSurface, OUT &supports_present ));

				if ( supports_present )
					curr_flags |= VK_QUEUE_PRESENT_BIT;
			}}

			if ( curr_flags == requiredFlags )
			{{
				requiredFlags	= curr_flags;
				familyIndex		= uint(i);
				return true;
			}}

			if ( EnumEq( curr_flags, requiredFlags ) and 
				 (compatible.first == 0 or BitSet<32>{{compatible.first}}.count() > BitSet<32>{{curr_flags}}.count()) )
			{{
				compatible = {{ curr_flags, uint(i) }};
			}}
		}}

		if ( compatible.first ) {{
			requiredFlags	= compatible.first;
			familyIndex		= compatible.second;
			return true;
		}}

		RETURN_ERR( "no suitable queue family found!" );
	}}

/*
=================================================
	_DestroyDevice
=================================================
*/
	void VulkanDevice::_DestroyDevice ()
	{{
		_BeforeDestroy();

		if ( _vkSurface ) {{
			vkDestroySurfaceKHR( _vkInstance, _vkSurface, null );
		}}

		if ( _vkDevice ) {{
			vkDestroyDevice( _vkDevice, null );
			VulkanLoader::ResetDevice( OUT _deviceFnTable );
		}}

		if ( _vkInstance )
		{{
			if ( not _usedSharedInstance )
				vkDestroyInstance( _vkInstance, null );

			VulkanLoader::Unload();
		}}

		_vkSurface			= VK_NULL_HANDLE;
		_vkInstance			= VK_NULL_HANDLE;
		_vkPhysicalDevice	= VK_NULL_HANDLE;
		_vkDevice			= VK_NULL_HANDLE;
		_usedSharedInstance	= false;
		_vkQueues.clear();

		_AfterDestroy();
	}}

}}	// FGC
"""


FEATURE_TYPES = [
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_BLEND_OPERATION_ADVANCED_FEATURES_EXT",
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_CONDITIONAL_RENDERING_FEATURES_EXT",
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MESH_SHADER_FEATURES_NV",
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_INLINE_UNIFORM_BLOCK_FEATURES_EXT",
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_REPRESENTATIVE_FRAGMENT_TEST_FEATURES_NV",
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADER_BARYCENTRIC_FEATURES_KHR",
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_IMAGE_FOOTPRINT_FEATURES_NV",
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADING_RATE_IMAGE_FEATURES_NV",
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTENDED_DYNAMIC_STATE_FEATURES_EXT",
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTENDED_DYNAMIC_STATE_2_FEATURES_EXT",
	"VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COLOR_WRITE_ENABLE_FEATURES_EXT",
]


def get_feature_items(feature_type):
    assert feature_type.startswith("VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_")
    items = feature_type.split("_")
    has_postfix = (items[-2] == "FEATURES")

    if has_postfix:
        struct_name = "Vk" + "".join([item.capitalize() for item in items[3:-1]] + [items[-1]])
    else:
        struct_name = "Vk" + "".join([item.capitalize() for item in items[3:]])

    struct_member = "".join([items[5].lower()]+[item.capitalize() for item in items[6:-2 if has_postfix else -1]])

    feature_name = "VK_" + (items[-1] if has_postfix else "KHR") + "_" + "_".join(items[5: -2 if has_postfix else -1]) + "_EXTENSION_NAME"

    func_name = "GetDevice" + ''.join([item.capitalize() for item in items[5: -1 if has_postfix else 0]])

    return (feature_type, struct_name, struct_member, feature_name, func_name)


def get_feature_declarations(items):
    indent = "\t\t\t"
    return '\n'.join(["{0}{1} {2};".format(indent, item[1], item[2]) for item in items])


def get_function_definitions(items):
    indent = "\t\t"
# ND_ VkPhysicalDeviceRepresentativeFragmentTestFeaturesNV const&	GetDeviceRepresentativeFragmentTestFeatures ()	const	{ return _features.representativeFragmentTest; }
    return '\n'.join(["{0}ND_ {1} const& {2}() const {{ return _features.{3}; }}".format(indent, item[1], item[4], item[2]) for item in items])


def get_use_extensions(items):
    FMT = """if (ext == {FEATURE_NAME})
			{{
				*next_feat = *nextExt = &_features.{STRUCT_MEMBER};
				next_feat = nextExt = &_features.{STRUCT_MEMBER}.pNext;
				_features.{STRUCT_MEMBER}.sType = {FEATURE_TYPE};
			}}"""
    return '\n\t\t\telse '.join([FMT.format(FEATURE_NAME=item[3], STRUCT_MEMBER=item[2], FEATURE_TYPE=item[0]) for item in items])

def gen_header(items):
    s = VULKAN_DEVICE_H.format(**items)
    with open("VulkanDevice.h", "w") as f:
        f.write(s)

    s = VULKAN_DEVICE_CPP.format(**items)
    with open("VulkanDevice.cpp", "w") as f:
        f.write(s)


if __name__ == '__main__':
    items = [get_feature_items(feature_type) for feature_type in FEATURE_TYPES]
    values = {
        "FEATURE_DECLARATIONS" : get_feature_declarations(items),
        "FUNCTION_DEFINITIONS" : get_function_definitions(items),
        "USE_EXTENSIONS" : get_use_extensions(items),
    }

    gen_header(values)
#
#    for ft in FEATURE_TYPES:
#        r = get_feature_items(ft)
#        print(r)
