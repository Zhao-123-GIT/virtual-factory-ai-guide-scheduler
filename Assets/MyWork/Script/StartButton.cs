using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class StartButton : MonoBehaviour
{
    public ConveyorBelt conveyorBelt;
    public Robot_Function Robot;
    private void OnMouseDown()
    {
        conveyorBelt.feedIn = true;
        Robot.RobotWorking();
    }
}