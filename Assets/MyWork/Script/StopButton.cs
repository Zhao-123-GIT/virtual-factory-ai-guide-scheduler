using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class StopButton : MonoBehaviour
{
    public ConveyorBelt conveyorBelt_Function;

    private void OnMouseDown()
    {
        conveyorBelt_Function.feedIn = false;
    }

}