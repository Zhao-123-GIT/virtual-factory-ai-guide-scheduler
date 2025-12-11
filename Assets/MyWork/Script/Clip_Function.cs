using System;
using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting;
using UnityEngine;

public class Clip_Function : MonoBehaviour
{
    public GameObject clipBase;
    public GameObject leftClip;
    public GameObject rightClip;

    public GameObject targetObject;

    public float clipDistance = 0.01f;
    public float clipTime = 1f;

    public bool grabbed = false;
    bool working = false;

    GameObject triggedObject;
    GameObject clippedObject;

    [Range(-1, 1)]
    int grabDirection = 0;

    [Header("debug")]
    public KeyCode debugKeycode;

    private void Start()
    {
        clipBase.AddComponent<FixedJoint>();
        clipBase.GetComponent<Rigidbody>().isKinematic = true;        
    }


    public IEnumerator ClipFunction()
    {
        if (working == false)
        {
            if (grabDirection == 0)
            {
                grabDirection = 1;
            }
            else
            {
                grabDirection = -grabDirection;
            }

            working = true;

            // Implementation of gripper movement as described in "抓取物体流程"
            // Moving through interpolation over 60 frames for smooth animation
            for (int i = 0; i < 60; i++)
            {
                leftClip.transform.Translate(new Vector3(0, 0, -grabDirection * clipDistance / 60));
                rightClip.transform.Translate(new Vector3(0, 0, grabDirection * clipDistance / 60));

                yield return new WaitForSecondsRealtime(clipTime / 60);
            }

            working = false;

            // Object attachment/detachment logic as described in "抓取物体流程"
            // Using FixedJoint to connect/disconnect objects
            if (clipBase.GetComponent<FixedJoint>().connectedBody == null)
            {
                if (triggedObject != null)
                {
                    clippedObject = triggedObject;
                    clipBase.GetComponent<FixedJoint>().connectedBody = clippedObject.GetComponent<Rigidbody>();
                    grabbed = true;
                }
            }
            else
            {
                clippedObject.GetComponent<Rigidbody>().isKinematic = true;
                clippedObject.GetComponent<Rigidbody>().isKinematic = false;

                clippedObject = null;
                clipBase.GetComponent<FixedJoint>().connectedBody = null;
                grabbed = false;
            }
        }        
    }


    private void OnTriggerStay(Collider other)
    {
        if(other.name.Contains(targetObject.name))triggedObject = other.gameObject;        
    }


    public void ClipWorking()
    {
        if (working == false) 
        {
            StartCoroutine("ClipFunction");
        }
    }


    #region debug
    private void Update()
    {
        if (Input.GetKeyDown(debugKeycode))
        {
            ClipWorking();
        }
    }
    #endregion

}