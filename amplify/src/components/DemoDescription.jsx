function DemoDescription() {
  return (
    <section className="demo-description" aria-labelledby="demo-description-heading">
      <h2 id="demo-description-heading" className="demo-description__title">
        Description
      </h2>
      <p>
        Serverless demo that copies volcano camera images from{' '}
        <strong>GeoNet Aotearoa New Zealand Data</strong> into a private S3 bucket,
        attaches <strong>JSON metadata via Amazon S3 Annotations</strong>, and serves a
        filterable gallery through API Gateway + Amplify.
      </p>
      <p>
        Source images are read from the{' '}
        <a
          href="https://registry.opendata.aws/geonet/"
          target="_blank"
          rel="noopener noreferrer"
        >
          GeoNet open dataset on AWS
        </a>{' '}
        (<code>s3://geonet-open-data</code>) — part of the{' '}
        <strong>AWS Open Data Sponsorship Program</strong>, which hosts public datasets
        on S3 for free analysis without copying data out of AWS.
      </p>
      <p>
        This demo ingests the{' '}
        <a
          href="https://www.geonet.org.nz/volcano/cameras/tekaha"
          target="_blank"
          rel="noopener noreferrer"
        >
          Te Kaha
        </a>{' '}
        volcano camera (<code>TKAH.01</code>) on the Bay of Plenty coast — a west-facing
        webcam that views <strong>Whakaari/White Island</strong>, with images captured
        every 10 minutes.
      </p>
      <p>
        <strong>What this walkthrough is about:</strong> metadata lives{' '}
        <strong>on the S3 object</strong> — write at ingest, read at query time, filter in
        the gallery — without a separate metadata database (DynamoDB is optional).
      </p>
      <p>
        <strong>What this walkthrough is not about:</strong> production volcano monitoring
        or advanced image classification.
      </p>
    </section>
  );
}

export default DemoDescription;
