import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FileCheck,
  Shield,
  Zap,
  Clock,
  CheckCircle,
  ArrowRight,
  Building2,
  Users,
  Quote,
  Play,
  Loader2,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { FileUpload } from '@/components/FileUpload'
import { ValidationResults } from '@/components/ValidationResults'
import { useValidationStore, useValidate } from '@/hooks/useValidation'

export function Landing() {
  const { currentResult } = useValidationStore()
  const { t } = useTranslation()
  const validate = useValidate()
  const [loadingDemo, setLoadingDemo] = useState(false)

  const handleDemoValidation = async () => {
    setLoadingDemo(true)
    try {
      // Fetch the demo XRechnung file from public folder
      const response = await fetch('/demo-xrechnung.xml')
      const blob = await response.blob()
      const file = new File([blob], 'demo-xrechnung.xml', { type: 'application/xml' })
      validate.mutate(file)
    } catch (error) {
      console.error('Failed to load demo file:', error)
    } finally {
      setLoadingDemo(false)
    }
  }

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-primary-50 to-white py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 text-balance">
              {t('landing.hero.title')}{' '}
              <span className="text-primary-600">{t('landing.hero.titleHighlight')}</span>
            </h1>
            <p className="mt-6 text-lg md:text-xl text-gray-600 text-balance">
              {t('landing.hero.subtitle')}
            </p>

            {/* Upload Area */}
            <div className="mt-10 max-w-2xl mx-auto">
              {currentResult ? (
                <ValidationResults />
              ) : (
                <FileUpload />
              )}
            </div>

            {/* Trust badges */}
            <div className="mt-8 flex flex-wrap justify-center gap-6 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-success-500" />
                {t('landing.hero.badges.gdpr')}
              </div>
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-warning-500" />
                {t('landing.hero.badges.instant')}
              </div>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-primary-500" />
                {t('landing.hero.badges.available')}
              </div>
            </div>

            {/* Demo Button */}
            {!currentResult && (
              <div className="mt-6">
                <button
                  onClick={handleDemoValidation}
                  disabled={loadingDemo}
                  className="inline-flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors"
                >
                  {loadingDemo ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  {t('landing.hero.tryDemo')}
                </button>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-12 bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              {t('landing.testimonials.trusted')}
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <TestimonialCard
              quote={t('landing.testimonials.quote1.text')}
              author={t('landing.testimonials.quote1.author')}
              role={t('landing.testimonials.quote1.role')}
            />
            <TestimonialCard
              quote={t('landing.testimonials.quote2.text')}
              author={t('landing.testimonials.quote2.author')}
              role={t('landing.testimonials.quote2.role')}
            />
            <TestimonialCard
              quote={t('landing.testimonials.quote3.text')}
              author={t('landing.testimonials.quote3.author')}
              role={t('landing.testimonials.quote3.role')}
            />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
              {t('landing.features.title')}
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              {t('landing.features.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={FileCheck}
              title={t('landing.features.xrechnung.title')}
              description={t('landing.features.xrechnung.description')}
            />
            <FeatureCard
              icon={FileCheck}
              title={t('landing.features.zugferd.title')}
              description={t('landing.features.zugferd.description')}
            />
            <FeatureCard
              icon={Shield}
              title={t('landing.features.privacy.title')}
              description={t('landing.features.privacy.description')}
            />
            <FeatureCard
              icon={Zap}
              title={t('landing.features.fast.title')}
              description={t('landing.features.fast.description')}
            />
            <FeatureCard
              icon={Building2}
              title={t('landing.features.api.title')}
              description={t('landing.features.api.description')}
            />
            <FeatureCard
              icon={Users}
              title={t('landing.features.clients.title')}
              description={t('landing.features.clients.description')}
            />
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16 lg:py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
              {t('landing.howItWorks.title')}
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <StepCard
              number="1"
              title={t('landing.howItWorks.step1.title')}
              description={t('landing.howItWorks.step1.description')}
            />
            <StepCard
              number="2"
              title={t('landing.howItWorks.step2.title')}
              description={t('landing.howItWorks.step2.description')}
            />
            <StepCard
              number="3"
              title={t('landing.howItWorks.step3.title')}
              description={t('landing.howItWorks.step3.description')}
            />
          </div>
        </div>
      </section>

      {/* Standards Section */}
      <section className="py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
              {t('landing.standards.title')}
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              {t('landing.standards.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="card p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                XRechnung
              </h3>
              <ul className="space-y-3">
                <CheckItem text={t('landing.standards.xrechnung.item1')} />
                <CheckItem text={t('landing.standards.xrechnung.item2')} />
                <CheckItem text={t('landing.standards.xrechnung.item3')} />
                <CheckItem text={t('landing.standards.xrechnung.item4')} />
              </ul>
            </div>
            <div className="card p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                ZUGFeRD / Factur-X
              </h3>
              <ul className="space-y-3">
                <CheckItem text={t('landing.standards.zugferd.item1')} />
                <CheckItem text={t('landing.standards.zugferd.item2')} />
                <CheckItem text={t('landing.standards.zugferd.item3')} />
                <CheckItem text={t('landing.standards.zugferd.item4')} />
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 lg:py-24 bg-primary-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white">
            {t('landing.cta.title')}
          </h2>
          <p className="mt-4 text-lg text-primary-100">
            {t('landing.cta.subtitle')}
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/registrieren"
              className="btn btn-lg bg-white text-primary-600 hover:bg-gray-100"
            >
              {t('landing.cta.register')}
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
            <Link
              to="/preise"
              className="btn btn-lg bg-primary-700 text-white hover:bg-primary-800"
            >
              {t('landing.cta.viewPricing')}
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof FileCheck
  title: string
  description: string
}) {
  return (
    <div className="card-hover p-6">
      <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center mb-4">
        <Icon className="h-6 w-6 text-primary-600" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

function StepCard({
  number,
  title,
  description,
}: {
  number: string
  title: string
  description: string
}) {
  return (
    <div className="text-center">
      <div className="w-12 h-12 rounded-full bg-primary-600 text-white text-xl font-bold flex items-center justify-center mx-auto mb-4">
        {number}
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

function CheckItem({ text }: { text: string }) {
  return (
    <li className="flex items-center gap-2">
      <CheckCircle className="h-5 w-5 text-success-500 flex-shrink-0" />
      <span className="text-gray-700">{text}</span>
    </li>
  )
}

function TestimonialCard({
  quote,
  author,
  role,
}: {
  quote: string
  author: string
  role: string
}) {
  return (
    <div className="card p-6 relative">
      <Quote className="h-8 w-8 text-primary-100 absolute top-4 right-4" />
      <p className="text-gray-700 mb-4 relative z-10">&ldquo;{quote}&rdquo;</p>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
          <span className="text-primary-600 font-semibold text-sm">
            {author.split(' ').map(n => n[0]).join('')}
          </span>
        </div>
        <div>
          <p className="font-medium text-gray-900 text-sm">{author}</p>
          <p className="text-gray-500 text-xs">{role}</p>
        </div>
      </div>
    </div>
  )
}
