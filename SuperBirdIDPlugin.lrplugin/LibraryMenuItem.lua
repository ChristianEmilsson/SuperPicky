--[[
    慧眼选鸟 - Library Menu Item
    通过 图库 → 增效工具 菜单快速识别当前选中的照片
]]

local LrApplication = import 'LrApplication'
local LrDialogs = import 'LrDialogs'
local LrTasks = import 'LrTasks'
local LrHttp = import 'LrHttp'
local LrView = import 'LrView'
local LrBinding = import 'LrBinding'
local LrFunctionContext = import 'LrFunctionContext'
local LrColor = import 'LrColor'
local LrFileUtils = import 'LrFileUtils'

-- 插件名称
local PLUGIN_NAME = "慧眼选鸟"

-- 默认设置
local DEFAULT_API_URL = "http://127.0.0.1:5156"
local DEFAULT_TOP_K = 3

-- Unicode解码辅助函数
local function decodeUnicodeEscape(str)
    if not str then return str end

    local function unicodeToUtf8(code)
        code = tonumber(code, 16)
        if code < 0x80 then
            return string.char(code)
        elseif code < 0x800 then
            return string.char(
                0xC0 + math.floor(code / 0x40),
                0x80 + (code % 0x40)
            )
        elseif code < 0x10000 then
            return string.char(
                0xE0 + math.floor(code / 0x1000),
                0x80 + (math.floor(code / 0x40) % 0x40),
                0x80 + (code % 0x40)
            )
        end
        return "?"
    end

    return str:gsub("\\u(%x%x%x%x)", unicodeToUtf8)
end

-- 简单的JSON解析函数
local function parseJSON(jsonString)
    local result = {}

    local success = string.match(jsonString, '"success"%s*:%s*([^,}]+)')
    if success then
        result.success = (success == "true")
    end

    local resultsBlock = string.match(jsonString, '"results"%s*:%s*%[(.-)%]')
    if resultsBlock then
        result.results = {}

        for itemBlock in string.gmatch(resultsBlock, '{([^{}]*)}') do
            local item = {}

            local cn_name_raw = string.match(itemBlock, '"cn_name"%s*:%s*"([^"]*)"')
            local en_name_raw = string.match(itemBlock, '"en_name"%s*:%s*"([^"]*)"')
            local sci_name_raw = string.match(itemBlock, '"scientific_name"%s*:%s*"([^"]*)"')
            local desc_raw = string.match(itemBlock, '"description"%s*:%s*"([^"]*)"')

            item.cn_name = decodeUnicodeEscape(cn_name_raw)
            item.en_name = decodeUnicodeEscape(en_name_raw)
            item.scientific_name = decodeUnicodeEscape(sci_name_raw)
            item.description = decodeUnicodeEscape(desc_raw)

            local confStr = string.match(itemBlock, '"confidence"%s*:%s*([%d%.]+)')
            item.confidence = confStr and tonumber(confStr) or 0

            if item.cn_name then
                table.insert(result.results, item)
            end
        end
    end

    local error_raw = string.match(jsonString, '"error"%s*:%s*"([^"]*)"')
    result.error = decodeUnicodeEscape(error_raw)

    return result
end

-- 简单的JSON编码函数
local function encodeJSON(tbl)
    local parts = {}
    for k, v in pairs(tbl) do
        local key = '"' .. tostring(k) .. '"'
        local value
        if type(v) == "string" then
            value = '"' .. v:gsub('"', '\\"'):gsub('\\', '\\\\') .. '"'
        elseif type(v) == "boolean" then
            value = tostring(v)
        elseif type(v) == "number" then
            value = tostring(v)
        else
            value = '"' .. tostring(v) .. '"'
        end
        table.insert(parts, key .. ":" .. value)
    end
    return "{" .. table.concat(parts, ",") .. "}"
end

-- 识别照片
local function recognizePhoto(photo, apiUrl)
    local photoPath = photo:getRawMetadata("path")
    local photoName = photo:getFormattedMetadata("fileName") or "Unknown"

    if not LrFileUtils.exists(photoPath) then
        return {
            success = false,
            error = "文件不存在: " .. photoName,
            photoName = photoName
        }
    end

    local requestBody = encodeJSON({
        image_path = photoPath,
        use_yolo = true,
        use_gps = true,
        top_k = DEFAULT_TOP_K
    })

    local response, headers = LrHttp.post(
        apiUrl .. "/recognize",
        requestBody,
        {
            { field = "Content-Type", value = "application/json" }
        }
    )

    if not response then
        return {
            success = false,
            error = "API调用失败",
            photoName = photoName
        }
    end

    local result = parseJSON(response)
    result.photoName = photoName
    result.photo = photo

    return result
end

-- 保存识别结果到照片元数据
-- 写入 Title (鸟名) 和 Caption (描述)
local function saveRecognitionResult(photo, species, enName, scientificName, description)
    local catalog = LrApplication.activeCatalog()

    -- 构建 Title 内容：中文名 (英文名)
    local title = species .. " (" .. enName .. ")"

    -- 构建 Caption 内容：只写入简介
    local caption = description or ""

    catalog:withWriteAccessDo("保存鸟类识别结果", function()
        photo:setRawMetadata("title", title)
        -- 写入 Caption (描述)
        if caption ~= "" then
            photo:setRawMetadata("caption", caption)
        end
    end)
end

-- 显示结果选择对话框
local function showResultSelectionDialog(results, photoName)
    local selectedIndex = nil

    LrFunctionContext.callWithContext("resultSelectionDialog", function(context)
        local f = LrView.osFactory()
        local props = LrBinding.makePropertyTable(context)

        props.selectedBird = 1

        local candidateViews = {}

        for i, bird in ipairs(results) do
            local confidence = bird.confidence or 0
            local cnName = bird.cn_name or "未知"
            local enName = bird.en_name or ""
            
            local confColor
            if confidence >= 50 then
                confColor = LrColor(0.2, 0.7, 0.3)
            elseif confidence >= 20 then
                confColor = LrColor(0.8, 0.6, 0.1)
            else
                confColor = LrColor(0.6, 0.6, 0.6)
            end

            candidateViews[#candidateViews + 1] = f:row {
                spacing = f:control_spacing(),
                
                f:radio_button {
                    title = "",
                    value = LrView.bind { key = 'selectedBird', object = props },
                    checked_value = i,
                    width = 20,
                },
                
                f:column {
                    spacing = 2,
                    
                    f:row {
                        f:static_text {
                            title = string.format("%d.", i),
                            font = "<system/bold>",
                            width = 20,
                        },
                        f:static_text {
                            title = cnName,
                            font = "<system/bold>",
                        },
                        f:static_text {
                            title = string.format("  %.1f%%", confidence),
                            text_color = confColor,
                            font = "<system/bold>",
                        },
                    },
                    
                    f:static_text {
                        title = "    " .. enName,
                        text_color = LrColor(0.5, 0.5, 0.5),
                        font = "<system/small>",
                    },
                },
            }
            
            if i < #results then
                candidateViews[#candidateViews + 1] = f:spacer { height = 6 }
                candidateViews[#candidateViews + 1] = f:separator { fill_horizontal = 1 }
                candidateViews[#candidateViews + 1] = f:spacer { height = 6 }
            end
        end

        candidateViews[#candidateViews + 1] = f:spacer { height = 12 }
        candidateViews[#candidateViews + 1] = f:separator { fill_horizontal = 1 }
        candidateViews[#candidateViews + 1] = f:spacer { height = 8 }
        
        candidateViews[#candidateViews + 1] = f:row {
            f:radio_button {
                title = "",
                value = LrView.bind { key = 'selectedBird', object = props },
                checked_value = 0,
                width = 20,
            },
            f:static_text {
                title = "跳过此照片，不写入",
                text_color = LrColor(0.5, 0.5, 0.5),
            },
        }

        local candidatesGroup = f:column(candidateViews)

        local dialogContent = f:column {
            spacing = f:control_spacing(),
            fill_horizontal = 1,

            f:spacer { width = 350 },

            f:row {
                f:static_text {
                    title = photoName .. " 的识别结果",
                    font = "<system/bold>",
                },
            },
            
            f:spacer { height = 8 },
            f:separator { fill_horizontal = 1 },
            f:spacer { height = 12 },

            candidatesGroup,
            
            f:spacer { height = 8 },
        }

        local dialogResult = LrDialogs.presentModalDialog({
            title = PLUGIN_NAME,
            contents = dialogContent,
            actionVerb = "写入 EXIF",
            cancelVerb = "取消",
            resizable = true,
        })

        if dialogResult == "ok" then
            selectedIndex = props.selectedBird
        else
            selectedIndex = nil
        end
    end)

    return selectedIndex
end

-- 主函数
LrTasks.startAsyncTask(function()
    local catalog = LrApplication.activeCatalog()
    local targetPhoto = catalog:getTargetPhoto()

    -- 检查是否选中了照片
    if not targetPhoto then
        LrDialogs.message(PLUGIN_NAME,
            "请先选中一张照片",
            "warning")
        return
    end

    -- 检查是否选中了多张照片
    local selectedPhotos = catalog:getTargetPhotos()
    if #selectedPhotos > 1 then
        LrDialogs.message(PLUGIN_NAME,
            "一次只能识别一张照片\n\n" ..
            "当前选中: " .. #selectedPhotos .. " 张\n\n" ..
            "请只选中一张照片后重试",
            "warning")
        return
    end

    -- 检查API服务是否可用
    local healthCheck = LrHttp.get(DEFAULT_API_URL .. "/health")

    if not healthCheck or string.find(healthCheck, '"status"%s*:%s*"ok"') == nil then
        LrDialogs.message(PLUGIN_NAME,
            "无法连接到慧眼选鸟 API 服务\n\n" ..
            "请确保:\n" ..
            "1. 慧眼选鸟主程序已启动\n" ..
            "2. 识鸟 API 服务已开启",
            "error")
        return
    end

    -- 识别照片
    local result = recognizePhoto(targetPhoto, DEFAULT_API_URL)

    if result.success and result.results and #result.results > 0 then
        -- 显示结果选择对话框
        local selectedIndex = showResultSelectionDialog(result.results, result.photoName)

        if selectedIndex and selectedIndex > 0 then
            local selectedBird = result.results[selectedIndex]
            local species = selectedBird.cn_name or "未知"
            local enName = selectedBird.en_name or ""
            local scientificName = selectedBird.scientific_name or ""

            saveRecognitionResult(targetPhoto, species, enName, scientificName, selectedBird.description)
        end
    else
        local errorMsg = result.error or "未知错误"

        local failMsg = "无法识别此照片中的鸟类\n\n" ..
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n" ..
            "错误信息:\n" .. errorMsg .. "\n\n" ..
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n" ..
            "可能的原因:\n" ..
            "• 照片中没有鸟类或鸟类不清晰\n" ..
            "• 图片文件损坏或格式不支持\n" ..
            "• 识别模型未正确加载"

        LrDialogs.message(PLUGIN_NAME .. " - 识别失败", failMsg, "error")
    end
end)
