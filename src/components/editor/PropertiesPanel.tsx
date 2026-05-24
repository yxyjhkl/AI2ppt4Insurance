import { Type, PaintBucket, Move, RotateCw, Layers, Trash2, Sparkles, Lock, Unlock } from 'lucide-react'
import type { CanvasElement, EntranceEffectName } from '@/types'
import { ENTRANCE_EFFECT_LABELS } from '@/types'

interface Props {
  element: CanvasElement | null
  onUpdate: (updates: Partial<CanvasElement>) => void
  onDelete: () => void
}

const SHAPE_OPTIONS = ['rectangle', 'circle', 'diamond', 'triangle']
const FONT_FAMILIES = ['Arial', 'Helvetica', 'Times New Roman', 'Georgia', 'Courier New', 'Microsoft YaHei', 'SimSun']
const FONT_SIZES = [10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 42, 48, 56, 64, 72]

const shapeLabels: Record<string, string> = {
  rectangle: '矩形',
  circle: '圆形',
  diamond: '菱形',
  triangle: '三角形',
}

export function PropertiesPanel({ element, onUpdate, onDelete }: Props) {
  if (!element) {
    return (
      <div className="p-4 text-center text-gray-400 text-sm">
        <Move className="w-6 h-6 mx-auto mb-2 opacity-50" />
        选中元素以编辑属性
      </div>
    )
  }

  return (
    <div className="p-3 space-y-4 text-sm overflow-auto max-h-[calc(100vh-300px)]">
      <Section icon={Type} title="内容">
        {element.type === 'text' && (
          <textarea
            className="w-full min-h-[60px] p-2 text-xs border border-gray-200 rounded resize-none focus:outline-none focus:ring-1 focus:ring-primary-300"
            value={element.content}
            onChange={(e) => onUpdate({ content: e.target.value })}
          />
        )}
        {element.type === 'shape' && (
          <select
            className="input-field text-xs"
            value={element.content}
            onChange={(e) => onUpdate({ content: e.target.value })}
          >
            {SHAPE_OPTIONS.map(s => (
              <option key={s} value={s}>{shapeLabels[s] || s}</option>
            ))}
          </select>
        )}
        {element.type === 'image' && (
          <div className="space-y-2">
            <input
              className="input-field text-xs"
              value={element.content}
              onChange={(e) => onUpdate({ content: e.target.value })}
              placeholder="图片地址URL或base64..."
            />
            {/* 本地上传按钮 - 使用label包裹input */}
            <label className="flex items-center justify-center w-full px-3 py-2 border-2 border-dashed border-gray-300 rounded cursor-pointer hover:border-primary-400 hover:bg-primary-50 transition-colors">
              <span className="text-xs text-gray-500">点击选择本地图片</span>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) {
                    const reader = new FileReader()
                    reader.onload = (ev) => {
                      onUpdate({ content: ev.target?.result as string })
                    }
                    reader.readAsDataURL(file)
                  }
                }}
              />
            </label>
          </div>
        )}
        {element.type === 'table' && (
          <textarea
            className="w-full min-h-[60px] p-2 text-xs border border-gray-200 rounded resize-none focus:outline-none focus:ring-1 focus:ring-primary-300 font-mono"
            value={element.content}
            onChange={(e) => onUpdate({ content: e.target.value })}
            placeholder="列1|列2&#10;A|B"
          />
        )}
      </Section>

      <Section icon={PaintBucket} title="样式">
        <div className="grid grid-cols-2 gap-2">
          <ColorField label="文本" value={element.style.color || '#1f2937'}
            onChange={(v) => onUpdate({ style: { ...element.style, color: v } })} />
          <ColorField label="背景" value={element.style.backgroundColor || 'transparent'}
            onChange={(v) => onUpdate({ style: { ...element.style, backgroundColor: v } })} />
          {element.type === 'shape' && (
            <ColorField label="填充" value={element.style.fillColor || '#e5e7eb'}
              onChange={(v) => onUpdate({ style: { ...element.style, fillColor: v } })} />
          )}
          <ColorField label="边框" value={element.style.borderColor || '#d1d5db'}
            onChange={(v) => onUpdate({ style: { ...element.style, borderColor: v } })} />
        </div>

        {element.type === 'text' && (
          <div className="grid grid-cols-2 gap-2 mt-2">
            <div>
              <label className="text-[10px] text-gray-500 block">字体</label>
              <select className="input-field text-xs" value={element.style.fontFamily || 'Arial'}
                onChange={(e) => onUpdate({ style: { ...element.style, fontFamily: e.target.value } })}>
                {FONT_FAMILIES.map(f => (
                  <option key={f} value={f} style={{ fontFamily: f }}>{f}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-[10px] text-gray-500 block">字号</label>
              <select className="input-field text-xs" value={element.style.fontSize || 16}
                onChange={(e) => onUpdate({ style: { ...element.style, fontSize: Number(e.target.value) } })}>
                {FONT_SIZES.map(s => <option key={s} value={s}>{s}px</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] text-gray-500 block">粗细</label>
              <select className="input-field text-xs" value={element.style.fontWeight || 'normal'}
                onChange={(e) => onUpdate({ style: { ...element.style, fontWeight: e.target.value } })}>
                <option value="normal">常规</option>
                <option value="bold">粗体</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] text-gray-500 block">对齐</label>
              <select className="input-field text-xs" value={element.style.textAlign || 'left'}
                  onChange={(e) => onUpdate({ style: { ...element.style, textAlign: e.target.value as CanvasElement['style']['textAlign'] } })}>
                <option value="left">左对齐</option>
                <option value="center">居中</option>
                <option value="right">右对齐</option>
              </select>
            </div>
          </div>
        )}
      </Section>

      <Section icon={Move} title="位置与尺寸">
        <div className="grid grid-cols-2 gap-2">
          <NumberField label="X" value={Math.round(element.x)}
            onChange={(v) => onUpdate({ x: v })} />
          <NumberField label="Y" value={Math.round(element.y)}
            onChange={(v) => onUpdate({ y: v })} />
          <NumberField label="W" value={Math.round(element.width)}
            onChange={(v) => onUpdate({ width: v })} />
          <NumberField label="H" value={Math.round(element.height)}
            onChange={(v) => onUpdate({ height: v })} />
        </div>
      </Section>

      <Section icon={RotateCw} title="变换">
        <div className="grid grid-cols-2 gap-2">
          <NumberField label="旋转°" value={element.rotation}
            min={-360} max={360}
            onChange={(v) => onUpdate({ rotation: v })} />
          <div>
            <label className="text-[10px] text-gray-500 block">透明度</label>
            <input type="range" min={0} max={100}
              value={element.opacity}
              onChange={(e) => onUpdate({ opacity: Number(e.target.value) })}
              className="w-full" />
            <span className="text-[10px] text-gray-400">{element.opacity}%</span>
          </div>
        </div>
      </Section>

      <Section icon={Layers} title="层级">
        <div className="flex items-center space-x-2">
          <button onClick={() => onUpdate({ zIndex: element.zIndex - 1 })}
            className="btn-secondary text-xs px-2 py-1">下移一层</button>
          <button onClick={() => onUpdate({ zIndex: element.zIndex + 1 })}
            className="btn-secondary text-xs px-2 py-1">上移一层</button>
        </div>
      </Section>

      <Section icon={Sparkles} title="动画">
        <select
          className="input-field text-xs"
          value={element.animation || 'none'}
          onChange={(e) => onUpdate({ animation: (e.target.value === 'none' ? undefined : e.target.value) as EntranceEffectName })}
        >
          {(Object.keys(ENTRANCE_EFFECT_LABELS) as EntranceEffectName[]).map(k => (
            <option key={k} value={k}>{ENTRANCE_EFFECT_LABELS[k]}</option>
          ))}
        </select>
        {element.animation && element.animation !== 'none' && (
          <p className="text-[10px] text-gray-400 mt-1">
            导出 PPTX 时将在 PowerPoint 中播放此动画效果
          </p>
        )}
      </Section>

      <button onClick={() => onUpdate({ locked: !element.locked })}
        className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 text-xs text-amber-600 hover:bg-amber-50 rounded-lg border border-amber-200 transition-colors mb-1">
        {element.locked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
        <span>{element.locked ? '已锁定 (点击解锁)' : '锁定元素'}</span>
      </button>

      <button onClick={onDelete}
        className="w-full flex items-center justify-center space-x-1.5 px-3 py-2 text-xs text-red-600 hover:bg-red-50 rounded-lg border border-red-200 transition-colors">
        <Trash2 className="w-3.5 h-3.5" />
        <span>删除元素</span>
      </button>
    </div>
  )
}

function Section({ icon: Icon, title, children }: { icon: typeof Type; title: string; children: import('react').ReactNode }) {
  return (
    <div>
      <div className="flex items-center space-x-1.5 mb-2 text-xs font-medium text-gray-600">
        <Icon className="w-3.5 h-3.5" />
        <span>{title}</span>
      </div>
      {children}
    </div>
  )
}

function ColorField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex items-center space-x-1.5">
      <label className="text-[10px] text-gray-500 w-16 shrink-0">{label}</label>
      <input type="color" value={value === 'transparent' ? '#ffffff' : value}
        onChange={(e) => onChange(e.target.value)}
        className="w-7 h-7 p-0.5 border border-gray-200 rounded cursor-pointer" />
      <input className="input-field text-[10px] flex-1 min-w-0"
        value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  )
}

function NumberField({ label, value, min, max, onChange }: { label: string; value: number; min?: number; max?: number; onChange: (v: number) => void }) {
  return (
    <div>
      <label className="text-[10px] text-gray-500 block">{label}</label>
      <input type="number" value={value} min={min} max={max}
        onChange={(e) => onChange(Math.max(min ?? -9999, Math.min(max ?? 9999, Number(e.target.value))))}
        className="input-field text-xs w-full" />
    </div>
  )
}