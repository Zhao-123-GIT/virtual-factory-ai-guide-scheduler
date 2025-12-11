using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Move : MonoBehaviour
{
    public float moveSpeed = 3f; // 在 Inspector 可调的速度
    private int count = 0;       // 仅在脚本内部使用的计数器
    private readonly List<GameObject> spawnedCubes = new(); // 记录生成的方块

    void Start()
    {
        for (int i = 0; i < 5; i++)
        {
            GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.transform.position = new Vector3(i * 2, 0, 0); // 间隔2单位排列
            spawnedCubes.Add(cube);
        }
    }

    void Update()
    {
        // 按空格切换移动方向
        if (Input.GetKeyDown(KeyCode.Space))
        {
            moveSpeed = -moveSpeed;
            Debug.Log("方向切换，当前速度：" + moveSpeed);
        }

        // 按 R 键将颜色改为红色
        if (Input.GetKeyDown(KeyCode.R)){
            ChangeColor(Color.red);
        }else if (Input.GetKeyDown(KeyCode.G)){
            ChangeColor(Color.green);
        }else if (Input.GetKeyDown(KeyCode.B)){
            ChangeColor(Color.blue);
        }

        // 按物体“自身前方”每秒移动 moveSpeed 米（与帧率无关）
        transform.Translate(moveSpeed * Time.deltaTime * Vector3.forward);
        count++;
        if (count % 100 == 0)
        {
            Debug.Log("移动了100帧，当前速度：" + moveSpeed);
        }
    }

    // 封装变色逻辑（兼容 URP 的 _BaseColor）
    void ChangeColor(Color targetColor)
    {
        // 若当前物体有 Renderer，则优先给自身变色
        var selfRenderer = GetComponent<Renderer>();
        if (selfRenderer != null)
        {
            ApplyColor(selfRenderer, targetColor);
            return;
        }

        // 否则给生成的方块变色
        foreach (var go in spawnedCubes)
        {
            var rend = go != null ? go.GetComponent<Renderer>() : null;
            if (rend != null)
            {
                ApplyColor(rend, targetColor);
            }
        }
    }

    void ApplyColor(Renderer rend, Color c)
    {
        if (rend == null) return;
        var mat = rend.material;
        if (mat == null) return;
        if (mat.HasProperty("_BaseColor"))
        {
            mat.SetColor("_BaseColor", c); // URP Lit 默认主颜色属性
        }
        else
        {
            mat.color = c; // 兼容内置/其他材质
        }
    }
}