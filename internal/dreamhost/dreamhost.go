package dreamhost

import (
	"context"
	"fmt"
	log "github.com/sirupsen/logrus"
	dhapi "github.com/adamantal/go-dreamhost/api"
	"sigs.k8s.io/external-dns/endpoint"
	"sigs.k8s.io/external-dns/plan"
	"sigs.k8s.io/external-dns/provider"
	"strings"
)

type DreamhostProvider struct {
	provider.BaseProvider
	client				*dhapi.Client
	zoneIDNameMapper 	provider.ZoneIDName
	domainFilter 		endpoint.DomainFilter
	DryRun 				bool
}

// Configuration contains the Vultr provider's configuration.
type Configuration struct {
	ApiKey               string   `env:"DREAMHOST_API_KEY" required:"true"`
	DryRun               bool     `env:"DRY_RUN" default:"false"`
	DomainFilter         []string `env:"DOMAIN_FILTER" default:""`
	ExcludeDomains       []string `env:"EXCLUDE_DOMAIN_FILTER" default:""`
}

// Constructor

func NewProvider(providerConfig *Configuration) *DreamhostProvider {
	dhclient, err := dhapi.NewClient(providerConfig.ApiKey, nil)
	if err != nil {
		panic(err)
	}
	return &DreamhostProvider{
		client:       dhclient,
		DryRun:       providerConfig.DryRun,
		domainFilter: GetDomainFilter(*providerConfig),
	}
}

// Global functions

func GetDomainFilter(config Configuration) endpoint.DomainFilter {
	createMsg := "Creating Dreamhost provider with "
	if len(config.DomainFilter) > 0 {
		createMsg += fmt.Sprintf("include filter: '%s', ", strings.Join(config.DomainFilter, ","))
	}
	if len(config.ExcludeDomains) > 0 {
		createMsg += fmt.Sprintf("exclude filter: '%s', ", strings.Join(config.ExcludeDomains, ","))
	}
	log.Info(createMsg)
	return endpoint.NewDomainFilterWithExclusions(config.DomainFilter, config.ExcludeDomains)
}

// Functions called by the 

func (p *DreamhostProvider) Records(ctx context.Context) ([]*endpoint.Endpoint, error) {
	records, err := p.client.ListDNSRecords(ctx)
	if err != nil {
		return nil, err
	}

	var endpoints []*endpoint.Endpoint
	for _, r := range records {
		if provider.SupportedRecordType(string(r.Type)) && p.domainFilter.Match(r.Record) {
			endpoints = append(endpoints, endpoint.NewEndpoint(string(r.Record), string(r.Type), string(r.Value)))
		}
	}

	return endpoints, nil
}

func (p *DreamhostProvider) AdjustEndpoints(endpoints []*endpoint.Endpoint) ([]*endpoint.Endpoint, error) {
	adjustedEndpoints := []*endpoint.Endpoint{}
	for _, ep := range endpoints {
		adjustedTargets := endpoint.Targets{}
		for _, t := range ep.Targets {
			err := p.client.RemoveDNSRecord(context.Background(), dhapi.DNSRecordInput{
				Record: ep.DNSName,
				Type:   dhapi.RecordType(ep.RecordType),
				Value:  t,
			})
			if err != nil {
				log.Warning(err)
			}
			err = p.client.AddDNSRecord(context.Background(), dhapi.DNSRecordInput{
				Record: ep.DNSName,
				Type:   dhapi.RecordType(ep.RecordType),
				Value:  t,
			})
			if err != nil {
				log.Warning(err)
			} else { 
				adjustedTargets = append(adjustedTargets, t)
			}
		}
		ep.Targets = adjustedTargets
		adjustedEndpoints = append(adjustedEndpoints, ep)
	}
	return adjustedEndpoints, nil
}

func (p *DreamhostProvider) ApplyChanges(ctx context.Context, changes *plan.Changes) error {
	for _, ep := range append(changes.Delete, changes.UpdateOld...) {
		for _, t := range ep.Targets {
			err := p.client.RemoveDNSRecord(ctx, dhapi.DNSRecordInput{
				Record: ep.DNSName,
				Type:   dhapi.RecordType(ep.RecordType),
				Value:  t,
			})
			if err != nil {
				log.Warning(err)
			}
		}
	}
	for _, ep := range append(changes.Create, changes.UpdateNew...) {
		for _, t := range ep.Targets {
			err := p.client.AddDNSRecord(ctx, dhapi.DNSRecordInput{
				Record: ep.DNSName,
				Type:   dhapi.RecordType(ep.RecordType),
				Value:  t,
			})
			if err != nil {
				log.Warning(err)
			}
		}
	}
	return nil
}
