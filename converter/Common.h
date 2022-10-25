// Copyright (c) 2018-2020,  Zhirnov Andrey. For more information see 'LICENSE'

#pragma once

#include "stl/Common.h"
#include "stl/Stream/FileStream.h"
#include "stl/Algorithms/StringUtils.h"

#define VK_NO_PROTOTYPES
#include "vulkan/vulkan.h"

#include <filesystem>

#define UNKNOWN_PREV_IMG_LAYOUT ((VkImageLayout)0xffffffff)

namespace RDE
{
	using namespace FGC;
	namespace FS = std::filesystem;

	using EResourceType	= VkObjectType;
	using VkResourceID = uint64_t;
	//enum VkResourceID : uint64_t {};	// TODO

	enum class ContentID : uint
	{
		Unknown = ~0u
	};


	struct ImageLayouts
	{
		struct ImageRegionState
		{
			uint					dstQueueFamilyIndex;
			VkImageSubresourceRange	subresourceRange;
			VkImageLayout			oldLayout;
			VkImageLayout			newLayout;
		};

		VkResourceID			imageId;
		uint					queueFamilyIndex;
		Array<ImageRegionState>	subresourceStates;
		uint					layerCount;
		uint					levelCount;
		uint					sampleCount;
		VkExtent3D				extent;
		VkFormat				format;
	};

	enum FrameRefType
	{
		eFrameRef_None = 0,
		eFrameRef_PartialWrite = 1,
		eFrameRef_CompleteWrite = 2,
		eFrameRef_Read = 3,
		eFrameRef_ReadBeforeWrite = 4,
		eFrameRef_WriteBeforeRead = 5,
		eFrameRef_CompleteWriteAndDiscard = 6,
		eFrameRef_Unknown = 1000000000,
	};

	struct ImageState
	{
		struct ImageInfo
		{
			uint32_t layerCount;
			uint32_t levelCount;
			uint32_t sampleCount;
			VkExtent3D  extent;
			VkFormat format;
			VkImageType imageType;
			VkImageLayout initialLayout;
			VkSharingMode sharingMode;
		};
		struct ImageSubresourceStateForRange
		{
			struct ImageSubresourceRange
			{
				VkImageAspectFlags aspectMask;
				uint32_t baseMipLevel;
				uint32_t levelCount;
				uint32_t baseArrayLayer;
				uint32_t layerCount;
				uint32_t baseDepthSlice;
				uint32_t sliceCount;
                operator VkImageSubresourceRange() const
                {
                    return { aspectMask, baseMipLevel, levelCount, baseArrayLayer, layerCount };
                }
			};
			struct ImageSubresourceState
			{
				uint32_t oldQueueFamilyIndex;
				uint32_t newQueueFamilyIndex;
				VkImageLayout oldLayout;
				VkImageLayout newLayout;
				FrameRefType refType;

                ImageSubresourceState(uint32_t queueFamilyIndex, VkImageLayout layout, FrameRefType refType = eFrameRef_None)
                    : oldQueueFamilyIndex(queueFamilyIndex),
                    newQueueFamilyIndex(queueFamilyIndex),
                    oldLayout(layout),
                    newLayout(layout),
                    refType(refType)
                {
                }
				ImageSubresourceState() {}
			};
			ImageSubresourceRange range;
			ImageSubresourceState state;
		};
		VkResourceID			imageId;
		ImageInfo imageInfo;
		Array<ImageSubresourceStateForRange> subresourceStates;
		Array<VkImageMemoryBarrier> oldQueueFamilyTransfers;
		Array<VkImageMemoryBarrier> newQueueFamilyTransfers;

		void ImageState::ResetToOldState(VkImage image, Array<VkImageMemoryBarrier>& barriers) const;

        ImageState() {}
		ImageState(const ImageInfo& imageInfo, FrameRefType refType);
	};

	struct InitParams {
		String AppName;
		String EngineName;
		uint32_t AppVersion;
		uint32_t EngineVersion;
		uint32_t APIVersion;
		Array<String> Layers;
		Array<String> Extensions;
		VkInstance InstanceID;
	};

}	// RDE
