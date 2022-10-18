// Copyright (c) 2018-2020,  Zhirnov Andrey. For more information see 'LICENSE'

#include "Common.h"

#define VK_ACCESS_ALL_READ_BITS                                                        \
  (VK_ACCESS_INDIRECT_COMMAND_READ_BIT | VK_ACCESS_INDEX_READ_BIT |                    \
   VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT | VK_ACCESS_UNIFORM_READ_BIT |                  \
   VK_ACCESS_INPUT_ATTACHMENT_READ_BIT | VK_ACCESS_SHADER_READ_BIT |                   \
   VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT | \
   VK_ACCESS_TRANSFER_READ_BIT | VK_ACCESS_HOST_READ_BIT | VK_ACCESS_MEMORY_READ_BIT)
#define VK_ACCESS_ALL_WRITE_BITS                                                 \
  (VK_ACCESS_SHADER_WRITE_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT |           \
   VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT | VK_ACCESS_TRANSFER_WRITE_BIT | \
   VK_ACCESS_HOST_WRITE_BIT | VK_ACCESS_MEMORY_WRITE_BIT)

#define UNKNOWN_PREV_IMG_LAYOUT ((VkImageLayout)0xffffffff)

namespace RDE
{
    bool IsDepthAndStencilFormat(VkFormat f)
    {
        switch (f)
        {
        case VK_FORMAT_D16_UNORM_S8_UINT:
        case VK_FORMAT_D24_UNORM_S8_UINT:
        case VK_FORMAT_D32_SFLOAT_S8_UINT: return true;
        default: break;
        }

        return false;
    }

    bool IsStencilOnlyFormat(VkFormat f)
    {
        switch (f)
        {
        case VK_FORMAT_S8_UINT: return true;
        default: break;
        }

        return false;
    }

    bool IsDepthOnlyFormat(VkFormat f)
    {
        switch (f)
        {
        case VK_FORMAT_D16_UNORM:
        case VK_FORMAT_X8_D24_UNORM_PACK32:
        case VK_FORMAT_D32_SFLOAT: return true;
        default: break;
        }

        return false;
    }

    uint32_t GetYUVPlaneCount(VkFormat f)
    {
        switch (f)
        {
        case VK_FORMAT_G8_B8R8_2PLANE_420_UNORM:
        case VK_FORMAT_G8_B8R8_2PLANE_422_UNORM:
        case VK_FORMAT_G16_B16R16_2PLANE_420_UNORM:
        case VK_FORMAT_G16_B16R16_2PLANE_422_UNORM:
        case VK_FORMAT_G10X6_B10X6R10X6_2PLANE_420_UNORM_3PACK16:
        case VK_FORMAT_G10X6_B10X6R10X6_2PLANE_422_UNORM_3PACK16:
        case VK_FORMAT_G12X4_B12X4R12X4_2PLANE_420_UNORM_3PACK16:
        case VK_FORMAT_G12X4_B12X4R12X4_2PLANE_422_UNORM_3PACK16:
        case VK_FORMAT_G8_B8R8_2PLANE_444_UNORM:
        case VK_FORMAT_G10X6_B10X6R10X6_2PLANE_444_UNORM_3PACK16:
        case VK_FORMAT_G12X4_B12X4R12X4_2PLANE_444_UNORM_3PACK16:
        case VK_FORMAT_G16_B16R16_2PLANE_444_UNORM: return 2;
        case VK_FORMAT_G8_B8_R8_3PLANE_420_UNORM:
        case VK_FORMAT_G8_B8_R8_3PLANE_422_UNORM:
        case VK_FORMAT_G8_B8_R8_3PLANE_444_UNORM:
        case VK_FORMAT_G10X6_B10X6_R10X6_3PLANE_420_UNORM_3PACK16:
        case VK_FORMAT_G10X6_B10X6_R10X6_3PLANE_422_UNORM_3PACK16:
        case VK_FORMAT_G10X6_B10X6_R10X6_3PLANE_444_UNORM_3PACK16:
        case VK_FORMAT_G12X4_B12X4_R12X4_3PLANE_420_UNORM_3PACK16:
        case VK_FORMAT_G12X4_B12X4_R12X4_3PLANE_422_UNORM_3PACK16:
        case VK_FORMAT_G12X4_B12X4_R12X4_3PLANE_444_UNORM_3PACK16:
        case VK_FORMAT_G16_B16_R16_3PLANE_420_UNORM:
        case VK_FORMAT_G16_B16_R16_3PLANE_422_UNORM:
        case VK_FORMAT_G16_B16_R16_3PLANE_444_UNORM: return 3;

        default: break;
        }

        return 1;
    }

    VkImageAspectFlags FormatImageAspects(VkFormat fmt)
    {
        if (IsStencilOnlyFormat(fmt))
            return VK_IMAGE_ASPECT_STENCIL_BIT;
        else if (IsDepthOnlyFormat(fmt))
            return VK_IMAGE_ASPECT_DEPTH_BIT;
        else if (IsDepthAndStencilFormat(fmt))
            return VK_IMAGE_ASPECT_DEPTH_BIT | VK_IMAGE_ASPECT_STENCIL_BIT;
        else if (GetYUVPlaneCount(fmt) == 3)
            return VK_IMAGE_ASPECT_PLANE_0_BIT | VK_IMAGE_ASPECT_PLANE_1_BIT | VK_IMAGE_ASPECT_PLANE_2_BIT;
        else if (GetYUVPlaneCount(fmt) == 2)
            return VK_IMAGE_ASPECT_PLANE_0_BIT | VK_IMAGE_ASPECT_PLANE_1_BIT;
        else
            return VK_IMAGE_ASPECT_COLOR_BIT;
    }

    void SanitiseReplayImageLayout(VkImageLayout& layout)
    {
        // we don't replay with present layouts since we don't create actual swapchains. So change any
        // present layouts to general layouts
        if (layout == VK_IMAGE_LAYOUT_PRESENT_SRC_KHR || layout == VK_IMAGE_LAYOUT_SHARED_PRESENT_KHR)
            layout = VK_IMAGE_LAYOUT_GENERAL;
    }

    void ImageState::ResetToOldState(VkImage image, Array<VkImageMemoryBarrier>& barriers)
    {
        VkAccessFlags srcAccessMask = VK_ACCESS_ALL_WRITE_BITS;
        VkAccessFlags dstAccessMask = VK_ACCESS_ALL_READ_BITS;
        const uint32_t CLOSE_TRANSFERS_BATCH_INDEX = 0;
        const uint32_t MAIN_BATCH_INDEX = 1;
        const uint32_t ACQUIRE_BATCH_INDEX = 2;
        const uint32_t RESTORE_TRANSFERS_BATCH_INDEX = 3;
        //CloseTransfers(CLOSE_TRANSFERS_BATCH_INDEX, dstAccessMask, barriers, info);

        for (auto const& subIt : subresourceStates)//.begin(); subIt != subresourceStates.end(); ++subIt)
        {
            VkImageLayout oldLayout = subIt.state.newLayout;
            if (oldLayout == UNKNOWN_PREV_IMG_LAYOUT)
                oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
            VkImageLayout newLayout = subIt.state.oldLayout;
            //subIt.state.newLayout = subIt.state.oldLayout;
            if (newLayout == UNKNOWN_PREV_IMG_LAYOUT || newLayout == VK_IMAGE_LAYOUT_UNDEFINED)
            {
                // contents discarded, no barrier necessary
                continue;
            }
            SanitiseReplayImageLayout(oldLayout);
            SanitiseReplayImageLayout(newLayout);
            if (oldLayout != VK_IMAGE_LAYOUT_PREINITIALIZED && newLayout == VK_IMAGE_LAYOUT_PREINITIALIZED)
            {
                // Transitioning back to PREINITIALIZED; this is impossible, so transition to GENERAL instead.
                newLayout = VK_IMAGE_LAYOUT_GENERAL;
            }

            uint32_t srcQueueFamilyIndex = subIt.state.newQueueFamilyIndex;
            uint32_t dstQueueFamilyIndex = subIt.state.oldQueueFamilyIndex;

            if (srcQueueFamilyIndex == VK_QUEUE_FAMILY_EXTERNAL ||
                srcQueueFamilyIndex == VK_QUEUE_FAMILY_FOREIGN_EXT)
            {
                srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            }
            if (dstQueueFamilyIndex == VK_QUEUE_FAMILY_EXTERNAL ||
                dstQueueFamilyIndex == VK_QUEUE_FAMILY_FOREIGN_EXT)
            {
                dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            }

            //uint32_t submitQueueFamilyIndex = srcQueueFamilyIndex;

            if (imageInfo.sharingMode == VK_SHARING_MODE_EXCLUSIVE)
            {
                if (srcQueueFamilyIndex == VK_QUEUE_FAMILY_IGNORED)
                {
                    //submitQueueFamilyIndex = dstQueueFamilyIndex;
                    dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
                }
                else if (dstQueueFamilyIndex == VK_QUEUE_FAMILY_IGNORED)
                {
                    srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
                }
            }
            else
            {
                //if (submitQueueFamilyIndex == VK_QUEUE_FAMILY_IGNORED)
                //    submitQueueFamilyIndex = dstQueueFamilyIndex;
                srcQueueFamilyIndex = dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            }

            if (srcQueueFamilyIndex == dstQueueFamilyIndex && oldLayout == newLayout)
            {
                //subIt.state.newQueueFamilyIndex = subIt.state.oldQueueFamilyIndex;
                continue;
            }

            //if (submitQueueFamilyIndex == VK_QUEUE_FAMILY_IGNORED)
            //{
            //    RDCWARN(
            //        "ResetToOldState: barrier submitted to VK_QUEUE_FAMILY_IGNORED; defaulting to queue "
            //        "family %u",
            //        info.defaultQueueFamilyIndex);
            //    submitQueueFamilyIndex = info.defaultQueueFamilyIndex;
            //}
            //subIt.state.newQueueFamilyIndex = subIt.state.oldQueueFamilyIndex;

            //ImageSubresourceRange subRange = subIt->range();

            if (subIt.range.baseDepthSlice != 0)
            {
                // We can't issue barriers per depth slice, so skip the barriers for non-zero depth slices.
                // The zero depth slice barrier will implicitly cover the non-zerp depth slices.
                continue;
            }

            VkImageAspectFlags aspects = FormatImageAspects(imageInfo.format);
            if ((aspects & (VK_IMAGE_ASPECT_DEPTH_BIT | VK_IMAGE_ASPECT_STENCIL_BIT)) ==
                (VK_IMAGE_ASPECT_DEPTH_BIT | VK_IMAGE_ASPECT_STENCIL_BIT))
                //&& !info.separateDepthStencil)
            {
                // This is a subresource of a depth and stencil image, and
                // VK_KHR_separate_depth_stencil_layouts is not enabled, so the barrier needs to include both
                // depth and stencil aspects. We skip the stencil-only aspect and expand the barrier for the
                // depth-only aspect to include both depth and stencil aspects.
                if (subIt.range.aspectMask == VK_IMAGE_ASPECT_STENCIL_BIT)
                    continue;
                //if (subIt.range.aspectMask == VK_IMAGE_ASPECT_DEPTH_BIT)
                //    subIt.range.aspectMask |= VK_IMAGE_ASPECT_STENCIL_BIT;
            }

            VkImageMemoryBarrier barrier = {
                /* sType = */ VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
                /* pNext = */ NULL,
                /* srcAccessMask = */ srcAccessMask,
                /* dstAccessMask = */ dstAccessMask,
                /* oldLayout = */ oldLayout,
                /* newLayout = */ newLayout,
                /* srcQueueFamilyIndex = */ srcQueueFamilyIndex,
                /* dstQueueFamilyIndex = */ dstQueueFamilyIndex,
                /* image = wrappedHandle */ image,
                /* subresourceRange = */ subIt.range,
            };
            barriers.emplace_back(barrier);
            //barriers.AddWrapped(MAIN_BATCH_INDEX, submitQueueFamilyIndex, barrier);

            //// acquire the subresource in the dstQueueFamily, if necessary
            //if (barrier.srcQueueFamilyIndex != barrier.dstQueueFamilyIndex)
            //{
            //    barriers.AddWrapped(ACQUIRE_BATCH_INDEX, barrier.dstQueueFamilyIndex, barrier);
            //}
        }
        //RestoreTransfers(RESTORE_TRANSFERS_BATCH_INDEX, oldQueueFamilyTransfers, srcAccessMask, barriers,
        //    info);
    }

}	// RDE
