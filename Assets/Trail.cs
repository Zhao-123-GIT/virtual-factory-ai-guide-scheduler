using System.Collections.Generic;
using UnityEngine;

public class Trail : MonoBehaviour
{
    [Header("轨迹设置")]
    public int maxTrailLength = 10;  // 最大轨迹长度
    public bool showTrail = true;    // 是否显示轨迹
    public Color trailColor = Color.red;  // 轨迹颜色
    public float lineWidth = 0.1f;   // 线条宽度
    
    private List<Vector3> positions = new List<Vector3>();
    private LineRenderer lineRenderer;
    
    void Start()
    {
        // 创建 LineRenderer 组件用于绘制轨迹
        if (showTrail)
        {
            SetupLineRenderer();
        }
    }
    
    void Update()
    {
        // 记录当前位置（仅在实际移动时追加，避免重复点）
        if (positions.Count == 0 || Vector3.Distance(positions[positions.Count - 1], transform.position) > 0.001f)
        {
            positions.Add(transform.position);
        }
        
        // 限制轨迹长度
        if (positions.Count > maxTrailLength)
        {
            positions.RemoveAt(0);
        }
        
        // 更新轨迹显示
        if (showTrail && lineRenderer != null)
        {
            UpdateTrailVisual();
        }
    }
    
    void SetupLineRenderer()
    {
        lineRenderer = gameObject.AddComponent<LineRenderer>();
        // 使用 URP Unlit，若不可用则回退到 Sprites/Default
        var shader = Shader.Find("Universal Render Pipeline/Unlit");
        if (shader == null) shader = Shader.Find("Sprites/Default");
        lineRenderer.material = new Material(shader);
    
        // 同时设置材质颜色与顶点颜色，提升可见性
        if (lineRenderer.material.HasProperty("_BaseColor"))
        {
            lineRenderer.material.SetColor("_BaseColor", trailColor);
        }
        else
        {
            lineRenderer.material.color = trailColor;
        }
        lineRenderer.startColor = trailColor;
        lineRenderer.endColor = trailColor;
    
        lineRenderer.startWidth = lineWidth;
        lineRenderer.endWidth = lineWidth;
        lineRenderer.useWorldSpace = true;
        lineRenderer.sortingOrder = 1;
    
        // 提高线的端点/拐角质量，并使其面向相机
        lineRenderer.numCornerVertices = 2;
        lineRenderer.numCapVertices = 2;
        lineRenderer.alignment = LineAlignment.View;
    }
    
    void UpdateTrailVisual()
    {
        lineRenderer.positionCount = positions.Count;
        lineRenderer.SetPositions(positions.ToArray());
    }
    
    // 获取轨迹位置列表（供其他脚本使用）
    public List<Vector3> GetTrailPositions()
    {
        return new List<Vector3>(positions);
    }
    
    // 清空轨迹
    public void ClearTrail()
    {
        positions.Clear();
        if (lineRenderer != null)
        {
            lineRenderer.positionCount = 0;
        }
    }
    
    // 动态设置轨迹颜色
    public void SetTrailColor(Color newColor)
    {
        trailColor = newColor;
        if (lineRenderer != null)
        {
            lineRenderer.startColor = newColor;
            lineRenderer.endColor = newColor;
        }
    }
}