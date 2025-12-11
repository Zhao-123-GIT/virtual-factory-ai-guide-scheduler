using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting;
using UnityEngine;

public class Conveyor_Big : MonoBehaviour
{
    public ConveyorBelt_Big BeltBig_0;
    public Lift_Function Lifter_0;

    public float[] times;

    public int timeIndex;
    
    public int directionIndex;

    public bool working;

    public bool finished;

    private void Start()
    {
        timeIndex = 0;
        directionIndex = -1;
        working = false;
        finished = true;
  
    }    

    IEnumerator Transfering()
    {
        if (!working)
        {
            for(int i=0; i< times.Length; i++)
            {
                working = true;
                                
                BeltBig_0.direction = directionIndex;
                yield return new WaitForSecondsRealtime(times[timeIndex]);
                BeltBig_0.direction = 0;

                if (timeIndex < (times.Length - 1))
                {
                    timeIndex += 1;
                }
                else
                {
                    timeIndex = 0;
                }

                if (directionIndex == -1)
                {
                    Lifter_0.finished = false;
                    Lifter_0.feedIn = true;
                    Debug.Log("feedin");
                    yield return new WaitUntil(() => Lifter_0.finished);
                }


                if (timeIndex == (times.Length - 1))
                {
                    directionIndex = 1;
                }
                else
                {
                    directionIndex = -1;
                }

                working = false;
            }
            finished = true;
        }
    }


    public void Processing()
    {
        if (finished)
        {
            finished = false;
            StartCoroutine("Transfering");
        }
    }



    #region debug
    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Alpha4))
        {
            Processing();
        }
    }
    #endregion
}
