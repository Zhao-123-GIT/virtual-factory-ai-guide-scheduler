using TMPro;
using UnityEngine;

public class ConveyorBelt : MonoBehaviour
{
    public float speed = 0.1f;
    public bool feedIn = false;

    public string targetTag;

    Rigidbody rBody;

    private void Start()
    {
        rBody = GetComponent<Rigidbody>();
    }

    private void OnTriggerStay(Collider other)
    {
        if (feedIn)
        {
            if(other.CompareTag(targetTag))other.transform.Translate(-transform.right * Time.deltaTime * speed);
        }
    }

}