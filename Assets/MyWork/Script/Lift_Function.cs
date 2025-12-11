using System;
using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting;
using UnityEngine;
using UnityEngine.UI;

public class Lift_Function : MonoBehaviour
{
    public GameObject lifter;
    public ConveyorBelt conveyorBelt_Function;

    public float safeHeight= 0.18f;
    public float takeProductDepth= 0.202f;
    public float releaseProductDepth= 0.3f;

    public float[] releaseProductLength;
         
    public bool feedIn;
    public bool working;
    public bool finished;

    public float liftTime = 2;
    public float carryingTime = 2;
    public float deltaTime = 0.1f;

    public int productIndex = 0;


    Clip_Function clipper;

    [Range(-1, 1)]
    int moving_V ;

    [Range(-1, 1)]
    int moving_H; 

    private void Start()
    {
        clipper = GetComponent<Clip_Function>();
        working = false;
        finished = true;
        feedIn = false;
    }

    IEnumerator Lifting()
    {
        if (working == false)
        {
            if (moving_V == 0)
            {
                moving_V = 1;
            }
            else
            {
                moving_V = -moving_V;
            }

            working = true;

            float tempDepth;
            if (lifter.transform.localPosition.z == 0)
            {
                tempDepth = takeProductDepth;
            }
            else
            {
                tempDepth = releaseProductDepth;
            }

            for (int i = 0; i < 60; i++)
            {
                lifter.transform.Translate(new Vector3(0, -moving_V * tempDepth / 60, 0));
                yield return new WaitForSecondsRealtime(liftTime / 60);
            }
            working = false;
        }        
    }


    IEnumerator Carrying()
    {
        if (working == false)
        {
            if (moving_H == 0)
            {
                moving_H = 1;
            }
            else
            {
                moving_H = -moving_H;
            }

            if (lifter.transform.localPosition.y > safeHeight)
            {
                working = true;
                for (int i = 0; i < 60; i++)
                {
                    lifter.transform.Translate(new Vector3(0, 0, -moving_H * releaseProductLength[productIndex] / 60));
                    yield return new WaitForSecondsRealtime(carryingTime / 60);
                }
                working = false;
            }
        }
    }

    IEnumerator Working()
    {
        feedIn = false;

        yield return StartCoroutine("Lifting");
        yield return StartCoroutine(clipper.ClipFunction());
        yield return StartCoroutine("Lifting");
        yield return StartCoroutine("Carrying");
        yield return StartCoroutine("Lifting");
        yield return StartCoroutine(clipper.ClipFunction());
        yield return StartCoroutine("Lifting");
        yield return StartCoroutine("Carrying");

        feedIn = true;

        if (productIndex < releaseProductLength.Length-1)
        {
            productIndex += 1;
        }
        else
        {
            productIndex = 0;
            feedIn = false;
            finished = true;
        }
    }


    private void OnTriggerStay(Collider other)
    {
        conveyorBelt_Function.feedIn = false;

        if (feedIn && (!working))
        {
            StartCoroutine("Working");
        }
    }

    private void OnTriggerExit(Collider other)
    {
        conveyorBelt_Function.feedIn = true;
    }


    #region debug
    void LiftWorking()
    {
        if(working==false)  StartCoroutine("Lifting");        
    }

    void CarryWorking()
    {
        if (working == false)  StartCoroutine("Carrying");
    }

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Alpha2) )
        {
            LiftWorking();
        }

        if (Input.GetKeyDown(KeyCode.Alpha3))
        {
            CarryWorking();
        }
    }
    #endregion

}
