using UnityEngine;

public class ProductFeeder : MonoBehaviour
{
    public GameObject product;

    bool available=true;

    private void Start()
    {
        Produce();
    }

    private void OnTriggerExit(Collider other)
    {
        Produce();
    }


    void Produce()
    {
        if (available)
        {
            var temp = Instantiate(product, transform);
        }
    }
}
