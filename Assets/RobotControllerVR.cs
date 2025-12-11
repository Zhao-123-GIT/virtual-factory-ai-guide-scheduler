using UnityEngine;
using UnityEngine.InputSystem;

public class RobotControllerVR : MonoBehaviour
{
    [Header("Input Actions")]
    public InputActionProperty moveAction;   // 左摇杆
    public InputActionProperty turnAction;   // 右摇杆

    [Header("Movement Settings")]
    public float moveSpeed = 1.0f;
    public float turnSpeed = 60f;

    void Update()
    {
        // 获取输入值
        Vector2 moveInput = moveAction.action.ReadValue<Vector2>();
        Vector2 turnInput = turnAction.action.ReadValue<Vector2>();

        // 移动方向
        Vector3 move = new Vector3(moveInput.x, 0, moveInput.y) * moveSpeed * Time.deltaTime;
        transform.Translate(move, Space.Self);

        // 旋转
        float yaw = turnInput.x * turnSpeed * Time.deltaTime;
        transform.Rotate(0, yaw, 0);
    }
}
