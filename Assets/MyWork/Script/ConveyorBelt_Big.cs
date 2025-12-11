using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ConveyorBelt_Big : MonoBehaviour
{
    public float speed = 0.1f;
    public bool powerOn = true;
    [Range(-1,1)]
    public int direction = 0;

    public string targetTag;

    private void OnTriggerStay(Collider other)
    {
        if (powerOn)
        {            
            if (other.CompareTag(targetTag))
            {
                other.transform.Translate(transform.right * Time.deltaTime * speed * direction);               

            }        }
    }
}